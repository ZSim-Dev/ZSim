from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

import httpx


class IPCConfig:
    """Configuration for IPC server.

    Environment variables:
    - ZSIM_IPC_MODE: "uds" | "pipe" | "off" (default: platform dependent; unix: uds, win: pipe)
    - ZSIM_IPC_UDS_PATH: Path to the unix domain socket file
    - ZSIM_IPC_PIPE_NAME: Windows named pipe name (without \\.\\pipe\\ prefix)
    """

    def __init__(self) -> None:
        mode_env = os.getenv("ZSIM_IPC_MODE")
        if mode_env in {"uds", "pipe", "off"}:
            self.mode = mode_env  # type: ignore[assignment]
        else:
            self.mode = "pipe" if sys.platform == "win32" else "uds"

        uds_path_env = os.getenv("ZSIM_IPC_UDS_PATH")
        if uds_path_env:
            self.uds_path = Path(uds_path_env)
        else:
            self.uds_path = Path(tempfile.gettempdir()) / "zsim_api.sock"

        pipe_name_env = os.getenv("ZSIM_IPC_PIPE_NAME")
        self.pipe_name = pipe_name_env or "zsim_api"


class IPCServer:
    """IPC server that proxies requests to the ASGI app.

    On Unix: uses Unix Domain Socket (UDS) with a simple framed JSON protocol.
    On Windows: uses Named Pipe (pywin32 required). Falls back to loopback HTTP if not available.
    """

    def __init__(self, asgi_app: Any, config: IPCConfig | None = None) -> None:
        self.asgi_app = asgi_app
        self.config = config or IPCConfig()
        self._uds_server: asyncio.base_events.Server | None = None
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

    # --------------------------- Public API ---------------------------
    async def start(self) -> None:
        if self.config.mode == "off":
            return
        if self.config.mode == "uds":
            await self._start_uds()
        elif self.config.mode == "pipe":
            self._start_pipe()

    async def stop(self) -> None:
        if self._uds_server is not None:
            self._uds_server.close()
            await self._uds_server.wait_closed()
            self._uds_server = None
            try:
                if self.config.uds_path.exists():
                    self.config.uds_path.unlink()
            except Exception:
                pass

        if self._threads:
            self._stop_event.set()
            for t in self._threads:
                t.join(timeout=2.0)
            self._threads.clear()

    # --------------------------- Protocol ---------------------------
    @staticmethod
    def _encode_message(payload: dict[str, Any]) -> bytes:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        length = len(data).to_bytes(4, byteorder="big")
        return length + data

    @staticmethod
    async def _read_exactly(reader: asyncio.StreamReader, n: int) -> bytes:
        data = await reader.readexactly(n)
        return data

    @staticmethod
    async def _read_message(reader: asyncio.StreamReader) -> dict[str, Any]:
        length_bytes = await IPCServer._read_exactly(reader, 4)
        length = int.from_bytes(length_bytes, byteorder="big")
        if length <= 0 or length > 32 * 1024 * 1024:
            raise ValueError("invalid frame length")
        data = await IPCServer._read_exactly(reader, length)
        return json.loads(data.decode("utf-8"))

    # --------------------------- UDS Server ---------------------------
    async def _start_uds(self) -> None:
        uds_path = self.config.uds_path
        try:
            if uds_path.exists():
                uds_path.unlink()
        except FileNotFoundError:
            pass
        uds_path.parent.mkdir(parents=True, exist_ok=True)

        async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            try:
                while True:
                    try:
                        request = await self._read_message(reader)
                    except (asyncio.IncompleteReadError, ConnectionResetError):
                        break
                    response = await self._dispatch_request(request)
                    writer.write(self._encode_message(response))
                    await writer.drain()
            finally:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

        self._uds_server = await asyncio.start_unix_server(handle_client, path=str(uds_path))

    # ------------------------ Windows Named Pipe ----------------------
    def _start_pipe(self) -> None:
        try:
            import win32file  # type: ignore[import-not-found]
            import win32pipe  # type: ignore[import-not-found]
            import pywintypes  # type: ignore[import-not-found]
        except Exception:
            # pywin32 not available; skip starting a pipe server
            return

        pipe_path = rf"\\.\pipe\{self.config.pipe_name}"

        def worker() -> None:
            while not self._stop_event.is_set():
                try:
                    handle = win32pipe.CreateNamedPipe(
                        pipe_path,
                        win32pipe.PIPE_ACCESS_DUPLEX,
                        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                        win32pipe.PIPE_UNLIMITED_INSTANCES,
                        1024 * 1024,
                        1024 * 1024,
                        0,
                        None,
                    )
                    try:
                        win32pipe.ConnectNamedPipe(handle, None)
                    except pywintypes.error:
                        win32file.CloseHandle(handle)
                        continue

                    # Each client handled sequentially in this worker; spawn new thread for next one
                    threading.Thread(target=self._handle_pipe_client, args=(handle,), daemon=True).start()
                except Exception:
                    # Prevent tight loop on unexpected errors
                    self._stop_event.wait(0.2)

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        self._threads.append(t)

    def _handle_pipe_client(self, handle: Any) -> None:
        try:
            import win32file  # type: ignore[import-not-found]
        except Exception:
            return

        try:
            while not self._stop_event.is_set():
                # Read 4-byte length
                hr, length_bytes = win32file.ReadFile(handle, 4)
                if hr != 0:
                    break
                length = int.from_bytes(length_bytes, byteorder="big")
                if length <= 0 or length > 32 * 1024 * 1024:
                    break
                hr, data = win32file.ReadFile(handle, length)
                if hr != 0:
                    break
                request = json.loads(data.decode("utf-8"))
                # Dispatch synchronously inside thread
                response = asyncio.run(self._dispatch_request(request))
                resp_bytes = self._encode_message(response)
                win32file.WriteFile(handle, resp_bytes)
        except Exception:
            pass
        finally:
            try:
                win32file.CloseHandle(handle)
            except Exception:
                pass

    # --------------------------- Dispatcher ---------------------------
    async def _dispatch_request(self, request: dict[str, Any]) -> dict[str, Any]:
        method: str = request.get("method", "GET")
        path: str = request.get("path", "/")
        query: dict[str, Any] = request.get("query", {})
        headers: dict[str, str] = request.get("headers", {})
        body: bytes | str | None = request.get("body")
        if isinstance(body, str):
            body_bytes: bytes | None = body.encode("utf-8")
        else:
            body_bytes = body

        async with httpx.AsyncClient(app=self.asgi_app, base_url="http://ipc") as client:
            try:
                resp = await client.request(
                    method=method,
                    url=path,
                    params=query,
                    headers=headers,
                    content=body_bytes,
                )
                return {
                    "status": resp.status_code,
                    "headers": dict(resp.headers),
                    "body": resp.content.decode("utf-8", errors="replace"),
                }
            except Exception as exc:
                return {
                    "status": 500,
                    "headers": {"content-type": "application/json"},
                    "body": json.dumps({"error": str(exc)}),
                }


__all__ = ["IPCConfig", "IPCServer"]


