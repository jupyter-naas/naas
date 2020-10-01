from naas.types import t_add, t_notebook, t_job, t_health, t_scheduler
import getpass
import pytest  # noqa: F401
import json
import uuid
import os
from shutil import copy2

user = getpass.getuser()
env_data = {
    "status": "healthy",
    "JUPYTERHUB_USER": user,
    "JUPYTERHUB_URL": "localhost:5000",
    "PUBLIC_PROXY_API": "localhost:5001",
    "NOTIFICATIONS_API": "localhost:5002",
    "TZ": "Europe/Paris",
}
status_data = {"status": "running"}


async def test_init(test_cli):
    response = await test_cli.get("/env")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == env_data


async def test_sheduler(test_cli):
    response = await test_cli.get("/scheduler/status")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == status_data


async def test_asset(test_cli):
    response = await test_cli.get("/asset/up.png")
    assert response.status == 200
    # TODO add more test


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


async def test_logs(test_cli):
    response = await test_cli.get("/log")
    assert response.status == 200
    logs = await response.json()
    assert logs.get("totalRecords") == 2
    status = logs.get("data")[0].get("status")
    assert status == "init API"


async def test_scheduler(test_cli, tmp_path):
    recur = "* * * * *"
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
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_add
    # TODO test scheduler result
    # time.sleep(60)
    # response = await test_cli.get(f"/{t_job}")
    # assert response.status == 200
    # resp_json = await response.json()
    # print('resp_json', resp_json)
    # assert res_job.get("type") == t_scheduler
    # assert res_job.get('path') == new_path
    # assert res_job.get('value') == recur
    # assert res_job.get('status') == t_health
