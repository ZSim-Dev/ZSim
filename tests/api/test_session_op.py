import json
import shutil
from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi import BackgroundTasks
from fastapi.testclient import TestClient

from zsim.api import app
from zsim.api_src.routes import session_op
from zsim.api_src.services.database.session_db import get_session_db
from zsim.define import results_dir
from zsim.models.session.session_create import Session
from zsim.models.session.session_run import SessionRun
from zsim.lib_webui import process_parallel_data as webui_parallel_data
from zsim.lib_webui.process_simulator import generate_parallel_args
from zsim.utils.process_parallel_data import judge_parallel_result, merge_parallel_dmg_data

client = TestClient(app)


@pytest.fixture
def session_data():
    return {
        "session_id": "test_session",
        "session_name": "Test Session",
        "session_type": "test",
        "apl_file_path": "data/APL/test_apl.toml",
        "character_config_path": "test/path",
        "enemy_config_path": "test/path",
        "simulation_config_path": "test/path",
    }


@pytest.fixture
def session_run_data():
    return {
        "common_config": {
            "session_id": "test_session",
            "char_config": [
                {"name": "仪玄"},
                {"name": "耀嘉音"},
                {"name": "扳机"},
            ],
            "enemy_config": {"index_id": 11412, "adjustment_id": 22412},
            "apl_path": "zsim/data/APLData/仪玄-耀嘉音-扳机.toml",
        },
        "mode": "normal",
    }


@pytest.mark.asyncio
async def test_create_session(session_data):
    db = await get_session_db()
    await db.delete_session("test_session")

    response = client.post("/api/sessions/", json=session_data)
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test_session"


@pytest.mark.asyncio
async def test_read_sessions(session_data):
    db = await get_session_db()
    await db.delete_session("test_session")
    session = Session(**session_data)
    await db.add_session(session)

    response = client.get("/api/sessions/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_read_session(session_data):
    db = await get_session_db()
    await db.delete_session("test_session")
    session = Session(**session_data)
    await db.add_session(session)

    response = client.get(f"/api/sessions/{session_data['session_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_data["session_id"]


@pytest.mark.asyncio
async def test_get_session_status(session_data):
    db = await get_session_db()
    await db.delete_session("test_session")
    session = Session(**session_data)
    await db.add_session(session)

    response = client.get(f"/api/sessions/{session_data['session_id']}/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "result" in data


@pytest.mark.asyncio
async def test_run_session(session_data, session_run_data):
    db = await get_session_db()
    await db.delete_session("test_session")
    session = Session(**session_data)
    await db.add_session(session)

    response = client.post(
        f"/api/sessions/{session_data['session_id']}/run?test_mode=true", json=session_run_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Session started successfully"

    # Check that the session status is now "completed"
    response = client.get(f"/api/sessions/{session_data['session_id']}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_stop_session(session_data, session_run_data):
    db = await get_session_db()
    await db.delete_session("test_session")
    session = Session(**session_data)
    session.status = "running"
    await db.add_session(session)

    response = client.post(f"/api/sessions/{session_data['session_id']}/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"


@pytest.mark.asyncio
async def test_update_session(session_data):
    db = await get_session_db()
    await db.delete_session("test_session")
    session = Session(**session_data)
    await db.add_session(session)

    updated_data = session_data.copy()
    updated_data["session_name"] = "Updated Test Session"

    response = client.put(f"/api/sessions/{session_data['session_id']}", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["session_name"] == "Updated Test Session"


@pytest.mark.asyncio
async def test_delete_session(session_data):
    db = await get_session_db()
    await db.delete_session("test_session")
    session = Session(**session_data)
    await db.add_session(session)

    response = client.delete(f"/api/sessions/{session_data['session_id']}")
    assert response.status_code == 204

    response = client.get(f"/api/sessions/{session_data['session_id']}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_parallel_run_writes_config_and_merge(session_data, monkeypatch):
    session_id = "parallel_test_session"
    result_dir_path = Path(results_dir) / session_id
    if result_dir_path.exists():
        shutil.rmtree(result_dir_path)

    db = await get_session_db()
    await db.delete_session(session_id)

    session_payload = session_data.copy()
    session_payload["session_id"] = session_id
    session = Session(**session_payload)
    await db.add_session(session)

    class DummySimController:
        def generate_parallel_args(self, _session, _session_run):
            return [None]

        async def put_into_queue(self, *_args, **_kwargs):
            return None

        async def execute_simulation_test(self):
            return []

        async def execute_simulation(self):
            return []

    monkeypatch.setattr(session_op, "SimController", DummySimController)

    session_run_payload = {
        "stop_tick": 10,
        "mode": "parallel",
        "common_config": {
            "session_id": session_id,
            "char_config": [
                {"name": "仪玄"},
                {"name": "耀嘉音"},
                {"name": "扳机"},
            ],
            "enemy_config": {"index_id": 11412, "adjustment_id": 22412},
            "apl_path": "zsim/data/APLData/仪玄-耀嘉音-扳机.toml",
        },
        "parallel_config": {
            "enable": True,
            "adjust_char": 1,
            "func": "attr_curve",
            "func_config": {
                "sc_range": [0, 0],
                "sc_list": ["scATK_percent"],
                "remove_equip_list": [],
            },
        },
    }

    session_run = SessionRun(**session_run_payload)
    background_tasks = BackgroundTasks()

    try:
        response = await session_op.run_session(
            session_id,
            session_run,
            background_tasks,
            db,
            test_mode=True,
        )
        assert response["code"] == 0

        config_path = result_dir_path / ".parallel_config.json"
        assert config_path.exists()

        config_data = json.loads(config_path.read_text(encoding="utf-8"))
        assert config_data["enabled"] is True
        assert config_data["adjust_sc"]["enabled"] is True
        assert config_data["adjust_sc"]["sc_range"] == [0, 0]
        assert config_data["adjust_sc"]["sc_list"] == ["scATK_percent"]
        assert config_data["adjust_weapon"]["enabled"] is False
        assert config_data["func_config"] == session_run_payload["parallel_config"]["func_config"]

        sub_dir = result_dir_path / "attr_curve_sample"
        sub_dir.mkdir(parents=True, exist_ok=True)
        (sub_dir / "sub.parallel_config.json").write_text(
            json.dumps(
                {
                    "adjust_char": "仪玄",
                    "sc_name": "scATK_percent",
                    "sc_value": 0,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (sub_dir / "damage_attribution.json").write_text(
            json.dumps(
                {
                    "仪玄": {
                        "direct_damage": 100.0,
                        "anomaly_damage": 50.0,
                    }
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        assert judge_parallel_result(session_id) is True

        alias_config = json.loads(config_path.read_text(encoding="utf-8"))
        alias_config["enable"] = alias_config.pop("enabled")
        alias_config["adjust_sc"]["enable"] = alias_config["adjust_sc"].pop("enabled")
        alias_config["adjust_weapon"]["enable"] = alias_config["adjust_weapon"].pop(
            "enabled"
        )
        config_path.write_text(
            json.dumps(alias_config, indent=4, ensure_ascii=False), encoding="utf-8"
        )

        assert judge_parallel_result(session_id) is True
        assert webui_parallel_data.judge_parallel_result(session_id) is True

        result = await merge_parallel_dmg_data(session_id)
        assert result is not None
        func, merged_data = result
        assert func == "attr_curve"
        assert merged_data["仪玄"]["scATK_percent"][0]["result"] == 150.0
    finally:
        await db.delete_session(session_id)
        if result_dir_path.exists():
            shutil.rmtree(result_dir_path)


def test_generate_parallel_args_accepts_enable_alias():
    args = list(
        generate_parallel_args(
            stop_tick=10,
            parallel_cfg={
                "func": "attr_curve",
                "adjust_char": 1,
                "adjust_sc": {
                    "enable": True,
                    "sc_range": [0, 0],
                    "sc_list": ["攻击力%"],
                    "remove_equip_list": [],
                },
                "adjust_weapon": {"enable": False, "weapon_list": []},
            },
            run_turn_uuid="uuid",
        )
    )

    assert len(args) == 1
    first_arg = args[0]
    assert first_arg.func == "attr_curve"
    assert first_arg.adjust_char == 1
    assert first_arg.sc_name == "scATK_percent"
