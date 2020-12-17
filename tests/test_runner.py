from naas.types import t_add, t_notebook, t_job, t_health, t_scheduler, t_asset
import getpass
import pytest  # noqa: F401

# import json
# import uuid
import os
from shutil import copy2

# import asyncio
from naas.runner import n_env
from naas import assets, api, scheduler
from syncer import sync


user = getpass.getuser()


def get_env():
    return {
        "status": "healthy",
        "JUPYTERHUB_USER": n_env.user,
        "JUPYTER_SERVER_ROOT": n_env.server_root,
        "JUPYTERHUB_URL": "http://localhost:5000",
        "PUBLIC_PROXY_API": "http://localhost:5001",
        "NOTIFICATIONS_API": "http://localhost:5002",
        "TZ": "Europe/Paris",
    }


status_data = {"status": "running"}


def mock_session(mocker, requests_mock, cur_path):
    mocker.patch(
        "ipykernel.get_connection_file",
        return_value="kernel-b1e19209-e251-4115-819e-7ab5bc4232b7.json",
    )
    mock_json = [
        {
            "kernel": {"id": "b1e19209-e251-4115-819e-7ab5bc4232b7"},
            "notebook": {"path": cur_path},
        },
    ]

    url = f"{n_env.hub_api}/user/{n_env.user}/api/sessions"
    requests_mock.register_uri("GET", url, json=mock_json, status_code=200)


def mock_job(requests_mock, test_cli):
    url_api = f"{n_env.api}/{t_job}"

    def post_json(request, context):
        data = request.json()
        res = sync(test_cli.post(f"/{t_job}", json=data))
        data_res = sync(res.json())
        return data_res

    def get_json(request, context):
        data = {}
        res = sync(test_cli.get(f"/{t_job}", json=data))
        data_res = sync(res.json())
        return data_res

    requests_mock.register_uri("GET", url_api, json=get_json, status_code=200)
    requests_mock.register_uri("POST", url_api, json=post_json, status_code=200)


# https://public.naas.ai/runner/runner/job
# https://public.naas.ai/runner/job


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


async def test_asset(mocker, requests_mock, test_cli, tmp_path):
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
    new_path = os.path.join(tmp_path, test_asset)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, cur_path)
    mock_job(requests_mock, test_cli)
    url = assets.add(new_path)
    assert url.startswith("http://localhost:5001/bWFydGluZG9uYWRpZXU=/asset/")
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_asset
    # filename = os.path.basename(new_path)
    # dirname = os.path.dirname(new_path)
    # filename = f"{t_asset}_{filename}"
    # new_path_out = os.path.join(dirname, filename)
    assert res_job.get("path") == new_path
    token = url.split("/")[-1]
    assert res_job.get("value") == token
    assert res_job.get("status") == t_add
    assert res_job.get("nbRun") == 0
    response = await test_cli.get(f"/{t_asset}/{token}")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar2"}


async def test_notebooks(mocker, requests_mock, test_cli, tmp_path):
    test_notebook = "tests/demo/demo_res_json.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_cli)
    url = api.add(new_path)
    assert url.startswith("http://localhost:5001/bWFydGluZG9uYWRpZXU=/notebook/")
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_notebook
    assert res_job.get("path") == new_path
    token = url.split("/")[-1]
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


async def test_scheduler(mocker, requests_mock, test_cli, tmp_path):
    recur = "*/5 * * * *"
    test_notebook = "tests/demo/demo_scheduler.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_cli)
    scheduler.add(new_path, recur)
    response = await test_cli.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_add
    # TODO fix
    # await asyncio.sleep(6)
    # response = await test_cli.get(f"/{t_job}")
    # assert response.status == 200
    # resp_json = await response.json()
    # assert res_job.get("type") == t_scheduler
    # assert res_job.get("path") == new_path
    # assert res_job.get("value") == recur
    # assert res_job.get("status") == t_start
    # await asyncio.sleep(3)
    # response = await test_cli.get(f"/{t_job}")
    # assert response.status == 200
    # resp_json = await response.json()
    # assert res_job.get("type") == t_scheduler
    # assert res_job.get("path") == new_path
    # assert res_job.get("value") == recur
    # assert res_job.get("status") == t_health
