from base64 import b64encode
from naas.runner.proxy import escape_kubernet
from naas.types import (
    t_add,
    t_notebook,
    t_job,
    t_health,
    t_scheduler,
    t_asset,
    t_secret,
)
import getpass
import pytest  # noqa: F401

# import json
# import uuid
import os
from shutil import copy2
from datetime import datetime, timedelta

# import asyncio
from naas.runner import n_env
from naas import assets, api, scheduler, secret
from syncer import sync


user = getpass.getuser()


def getUserb64():
    client_encoded = escape_kubernet(n_env.user)
    message_bytes = client_encoded.encode("ascii")
    base64_bytes = b64encode(message_bytes)
    username_base64 = base64_bytes.decode("ascii")
    return username_base64


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


def mock_secret(requests_mock, test_runner):
    url_api = f"{n_env.api}/{t_secret}"

    def post_json(request, context):
        data = request.json()
        res = sync(test_runner.post(f"/{t_secret}", json=data))
        data_res = sync(res.json())
        return data_res

    def get_json(request, context):
        data = {}
        res = sync(test_runner.get(f"/{t_secret}", json=data))
        data_res = sync(res.json())
        return data_res

    requests_mock.register_uri("GET", url_api, json=get_json, status_code=200)
    requests_mock.register_uri("POST", url_api, json=post_json, status_code=200)


def mock_job(requests_mock, test_runner):
    url_api = f"{n_env.api}/{t_job}"

    def post_json(request, context):
        data = request.json()
        res = sync(test_runner.post(f"/{t_job}", json=data))
        data_res = sync(res.json())
        return data_res

    def get_json(request, context):
        data = {}
        res = sync(test_runner.get(f"/{t_job}", json=data))
        data_res = sync(res.json())
        return data_res

    requests_mock.register_uri("GET", url_api, json=get_json, status_code=200)
    requests_mock.register_uri("POST", url_api, json=post_json, status_code=200)


# https://public.naas.ai/runner/runner/job
# https://public.naas.ai/runner/job


async def test_init(test_runner):
    response = await test_runner.get("/env")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == get_env()


async def test_scheduler_status(test_runner):
    response = await test_runner.get("/scheduler/status")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == status_data


async def test_secret(mocker, requests_mock, test_runner, tmp_path):
    mock_session(mocker, requests_mock, tmp_path)
    mock_secret(requests_mock, test_runner)
    response = await test_runner.get("/secret")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 0
    secret.add("test_3", "yolo")
    response = await test_runner.get("/secret")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    assert resp_json[0]["name"] == "test_3"
    assert resp_json[0]["secret"] == "yolo"
    res = secret.get("test_3")
    assert res == "yolo"
    secret.delete("test_3")
    res = secret.get("test_3")
    assert res in None
    response = await test_runner.get("/secret")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 0


async def test_asset(mocker, requests_mock, test_runner, tmp_path):
    response = await test_runner.get("/asset/naas_up.png")
    assert response.status == 200
    response = await test_runner.get("/asset/naas_down.png")
    assert response.status == 200
    response = await test_runner.get("/asset/naas_fav.svg")
    assert response.status == 200
    response = await test_runner.get("/asset/naas_logo.svg")
    assert response.status == 200
    response = await test_runner.get("/asset/naas_logo.png")
    assert response.status == 200
    test_asset = "tests/demo/demo.json"
    cur_path = os.path.join(os.getcwd(), test_asset)
    new_path = os.path.join(tmp_path, test_asset)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, cur_path)
    mock_job(requests_mock, test_runner)
    url = assets.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/asset/")
    response = await test_runner.get(f"/{t_job}")
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
    response = await test_runner.get(f"/{t_asset}/{token}")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar2"}


async def test_notebooks(mocker, requests_mock, test_runner, tmp_path):
    test_notebook = "tests/demo/demo_res_json.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = api.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    response = await test_runner.get(f"/{t_job}")
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
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar"}
    response = await test_runner.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_notebook
    assert res_job.get("path") == new_path
    assert res_job.get("value") == token
    assert res_job.get("status") == t_health
    assert res_job.get("nbRun") == 1
    response = await test_runner.post(f"/{t_notebook}/{token}", json={"foo": "bar"})
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar"}
    api.delete(new_path)
    response = await test_runner.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 0
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 404


async def test_logs(test_runner):
    response = await test_runner.get("/log")
    assert response.status == 200
    logs = await response.json()
    assert logs.get("totalRecords") == 2
    status = logs.get("data")[0].get("status")
    assert status == "init API"


async def test_scheduler(mocker, requests_mock, test_scheduler, tmp_path):
    curr_time = datetime.now()
    curr_time = curr_time + timedelta(seconds=2)
    sec = curr_time.strftime("%S")
    recur = f"{sec} * * * *"
    test_notebook = "tests/demo/demo_scheduler.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_scheduler)
    scheduler.add(new_path, recur)
    response = await test_scheduler.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_add
    # TODO fix
    # await asyncio.sleep(2)
    # response = await test_scheduler.get(f"/{t_job}")
    # assert response.status == 200
    # resp_json = await response.json()
    # assert res_job.get("type") == t_scheduler
    # assert res_job.get("path") == new_path
    # assert res_job.get("value") == recur
    # assert res_job.get("status") == t_start
    # await asyncio.sleep(3)
    # response = await test_scheduler.get(f"/{t_job}")
    # assert response.status == 200
    # resp_json = await response.json()
    # assert res_job.get("type") == t_scheduler
    # assert res_job.get("path") == new_path
    # assert res_job.get("value") == recur
    # assert res_job.get("status") == t_health
