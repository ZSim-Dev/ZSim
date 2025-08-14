from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path
import multiprocessing as mp

import pytest


def _server_process(pipe_name: str, ready: "mp.synchronize.Event", stop: "mp.synchronize.Event") -> None:
    os.environ["ZSIM_IPC_MODE"] = "pipe"
    os.environ["ZSIM_IPC_PIPE_NAME"] = pipe_name
    os.environ["ZSIM_DISABLE_ROUTES"] = "1"
    import zsim.api as zapi_inner
    import asyncio as _asyncio
    _asyncio.run(zapi_inner.app.router.startup())
    try:
        ready.set()
        stop.wait()
    finally:
        _asyncio.run(zapi_inner.app.router.shutdown())


async def _uds_request(socket_path: Path, payload: dict[str, object]) -> dict[str, object]:
    reader, writer = await asyncio.open_unix_connection(path=str(socket_path))

    try:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = len(data).to_bytes(4, byteorder="big")
        writer.write(header + data)
        await writer.drain()

        length_bytes = await reader.readexactly(4)
        length = int.from_bytes(length_bytes, byteorder="big")
        body = await reader.readexactly(length)
        return json.loads(body.decode("utf-8"))
    finally:
        writer.close()
        await writer.wait_closed()


def _pipe_request(pipe_path: str, payload: dict[str, object]) -> dict[str, object]:
    import win32file  # type: ignore[import-not-found]

    data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = len(data).to_bytes(4, byteorder="big")
    buf = header + data

    handle = win32file.CreateFile(
        pipe_path,
        0xC0000000,  # GENERIC_READ | GENERIC_WRITE
        0,
        None,
        3,  # OPEN_EXISTING
        0,
        None,
    )
    try:
        win32file.WriteFile(handle, buf)
        # Read response header
        hr, length_bytes = win32file.ReadFile(handle, 4)
        assert hr == 0
        length = int.from_bytes(length_bytes, byteorder="big")
        hr, body = win32file.ReadFile(handle, length)
        assert hr == 0
        return json.loads(body.decode("utf-8"))
    finally:
        try:
            win32file.CloseHandle(handle)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_ipc_health_ok() -> None:
    # Configure IPC mode before importing the app module
    if sys.platform == "win32":
        try:
            import win32file  # type: ignore[unused-ignore, import-not-found]  # noqa: F401
            import win32pipe  # type: ignore[unused-ignore, import-not-found]  # noqa: F401
        except Exception:
            pytest.skip("pywin32 not installed; skipping Named Pipe IPC test on Windows")

        pipe_name = f"zsim_test_pipe_{os.getpid()}"
        os.environ["ZSIM_IPC_MODE"] = "pipe"
        os.environ["ZSIM_IPC_PIPE_NAME"] = pipe_name
        os.environ["ZSIM_DISABLE_ROUTES"] = "1"
        pipe_path = rf"\\.\pipe\{pipe_name}"

        # Run server in a dedicated process to avoid event-loop interference on Windows
        ctx = mp.get_context("spawn")
        ready_event: mp.Event = ctx.Event()
        stop_event: mp.Event = ctx.Event()
        proc = ctx.Process(target=_server_process, args=(pipe_name, ready_event, stop_event))
        proc.start()
        try:
            # Wait for server startup
            assert ready_event.wait(timeout=5.0), "Server process failed to signal readiness"

            # Attempt request, retry a few times until pipe instance is created
            for _ in range(50):
                try:
                    resp = await asyncio.to_thread(
                        _pipe_request,
                        pipe_path,
                        {"method": "GET", "path": "/health", "query": {}, "headers": {}, "body": None},
                    )
                    break
                except Exception:
                    await asyncio.sleep(0.1)
            else:
                pytest.fail("Failed to connect to Named Pipe IPC server")

            assert resp["status"] == 200
            body = json.loads(resp["body"])  # type: ignore[arg-type]
            assert body["message"] == "ZSim API is running!"
        finally:
            stop_event.set()
            proc.join(timeout=2.0)
            if proc.is_alive():
                proc.terminate()

    else:
        uds_path = Path(tempfile.gettempdir()) / f"zsim_api_test_{os.getpid()}.sock"
        os.environ["ZSIM_IPC_MODE"] = "uds"
        os.environ["ZSIM_IPC_UDS_PATH"] = str(uds_path)
        os.environ["ZSIM_DISABLE_ROUTES"] = "1"

        # Reload zsim.api to apply env config
        if "zsim.api" in sys.modules:
            importlib.reload(sys.modules["zsim.api"])  # type: ignore[arg-type]
        else:
            import zsim.api  # noqa: F401

        import zsim.api as zapi

        await zapi.app.router.startup()

        # Wait for the socket file to appear
        for _ in range(40):
            if uds_path.exists():
                break
            await asyncio.sleep(0.05)

        assert uds_path.exists(), "UDS socket not created"

        resp = await _uds_request(
            uds_path, {"method": "GET", "path": "/health", "query": {}, "headers": {}, "body": None}
        )
        assert resp["status"] == 200
        body = json.loads(resp["body"])  # type: ignore[arg-type]
        assert body["message"] == "ZSim API is running!"

        await zapi.app.router.shutdown()
        try:
            if uds_path.exists():
                uds_path.unlink()
        except Exception:
            pass
