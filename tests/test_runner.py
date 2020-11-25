from naas.types import t_add, t_notebook, t_job, t_health, t_scheduler, t_asset, t_start
import getpass
import pytest  # noqa: F401
import json
import uuid
import os
from shutil import copy2
import asyncio

user = getpass.getuser()


def get_env():
    return {
        "status": "healthy",
        "JUPYTERHUB_USER": os.environ["JUPYTERHUB_USER"],
        "JUPYTER_SERVER_ROOT": os.environ["JUPYTER_SERVER_ROOT"],
        "JUPYTERHUB_URL": "http://localhost:5000",
        "PUBLIC_PROXY_API": "http://localhost:5001",
        "NOTIFICATIONS_API": "http://localhost:5002",
        "TZ": "Europe/Paris",
    }


status_data = {"status": "running"}


async def test_init(test_cli):
    response = await test_cli.get("/env")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == get_env()


async def test_scheduler_status(test_cli):
    response = await test_cli.get("/scheduler/status")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == status_data


async def test_asset(test_cli, tmp_path):
    response = await test_cli.get("/asset/naas_up.png")
    assert response.status == 200
    response = await test_cli.get("/asset/naas_down.png")
    assert response.status == 200
    response = await test_cli.get("/asset/naas_fav.svg")
    assert response.status == 200
    response = await test_cli.get("/asset/naas_logo.svg")
    assert response.status == 200
    response = await test_cli.get("/asset/naas_logo.png")
    assert response.status == 200
    test_asset = "tests/demo/demo.json"
    cur_path = os.path.join(os.getcwd(), test_asset)
    token = str(uuid.uuid4())
    new_path = os.path.join(tmp_path, test_asset)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    job = {
        "type": t_asset,
        "path": new_path,
        "params": {},
        "value": token,
        "status": t_add,
    }
    response = await test_cli.post(f"/{t_job}", data=json.dumps(job))
    assert response.status == 200
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_asset
    assert res_job.get("path") == new_path
    assert res_job.get("value") == token
    assert res_job.get("status") == t_add
    assert res_job.get("nbRun") == 0
    response = await test_cli.get(f"/{t_asset}/{token}")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar2"}


async def test_notebooks(test_cli, tmp_path):
    test_notebook = "tests/demo/demo_res_json.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    token = str(uuid.uuid4())
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    job = {
        "type": t_notebook,
        "path": new_path,
        "params": {},
        "value": token,
        "status": t_add,
    }
    response = await test_cli.post(f"/{t_job}", data=json.dumps(job))
    assert response.status == 200
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_notebook
    assert res_job.get("path") == new_path
    assert res_job.get("value") == token
    assert res_job.get("status") == t_add
    assert res_job.get("nbRun") == 0
    response = await test_cli.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar"}
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_notebook
    assert res_job.get("path") == new_path
    assert res_job.get("value") == token
    assert res_job.get("status") == t_health
    assert res_job.get("nbRun") == 1
    response = await test_cli.post(f"/{t_notebook}/{token}", json={"foo": "bar"})
    assert response.status == 200
    resp_json = await response.json()


async def test_logs(test_cli):
    response = await test_cli.get("/log")
    assert response.status == 200
    logs = await response.json()
    assert logs.get("totalRecords") == 2
    status = logs.get("data")[0].get("status")
    assert status == "init API"


@pytest.fixture
async def test_scheduler(test_cli, tmp_path):
    recur = "*/5 * * * *"
    test_notebook = "tests/demo/demo_scheduler.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    job = {
        "type": t_scheduler,
        "path": new_path,
        "params": {},
        "value": recur,
        "status": t_add,
    }
    response = await test_cli.post(f"/{t_job}", data=json.dumps(job))
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json.get("status") == t_add
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_add
    await asyncio.sleep(6)
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_start
    await asyncio.sleep(3)
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_health
