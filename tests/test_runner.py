from base64 import b64encode
from naas.runner.proxy import escape_kubernet
from naas.types import (
    t_add,
    t_notebook,
    t_job,
    t_health,
    t_asset,
    t_secret,
)
import getpass
import pytest  # noqa: F401
import os
from shutil import copy2
from naas.runner import n_env
from naas import assets, api, secret
from syncer import sync


user = getpass.getuser()
seps = os.sep + os.altsep if os.altsep else os.sep


def getUserb64():
    client_encoded = escape_kubernet(n_env.user)
    message_bytes = client_encoded.encode("ascii")
    base64_bytes = b64encode(message_bytes)
    username_base64 = base64_bytes.decode("ascii")
    return username_base64


def get_env():
    return {
        "status": "healthy",
        "version": n_env.version,
        "JUPYTERHUB_USER": n_env.user,
        "JUPYTER_SERVER_ROOT": n_env.server_root,
        "JUPYTERHUB_URL": "http://localhost:5000",
        "PUBLIC_PROXY_API": "http://localhost:5001",
        "NOTIFICATIONS_API": "http://localhost:5002",
        "TZ": "Europe/Paris",
    }


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
        context.status_code = res.status
        return data_res

    def get_json(request, context):
        data = {}
        res = sync(test_runner.get(f"/{t_secret}", json=data))
        data_res = sync(res.json())
        context.status_code = res.status
        return data_res

    requests_mock.register_uri("GET", url_api, json=get_json, status_code=200)
    requests_mock.register_uri("POST", url_api, json=post_json, status_code=200)


def mock_job(requests_mock, test_runner):
    url_api = f"{n_env.api}/{t_job}"

    def post_json(request, context):
        data = request.json()
        res = sync(test_runner.post(f"/{t_job}", json=data))
        data_res = sync(res.json())
        context.status_code = res.status
        return data_res

    def get_json(request, context):
        data = request.qs
        res = sync(test_runner.get(f"/{t_job}", params=data))
        data_res = sync(res.json())
        context.status_code = res.status
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
    assert res is None
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
    path_test_asset = "tests/demo/demo.json"
    cur_path = os.path.join(os.getcwd(), path_test_asset)
    new_path = os.path.join(tmp_path, path_test_asset)
    strip_path = os.path.splitdrive(new_path)[1].lstrip(seps)
    real_path = os.path.join(tmp_path, "pytest_tmp", ".naas", strip_path)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    assert os.path.isfile(new_path)
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
    assert res_job.get("path") == real_path
    token = url.split("/")[-1]
    assert res_job.get("value") == token
    assert res_job.get("status") == t_add
    assert res_job.get("nbRun") == 0
    response = await test_runner.get(f"/{t_asset}/{token}")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar2"}
    assert os.path.isfile(real_path)
    assets.get(new_path)
    filename = os.path.basename(new_path)
    dirname = os.path.dirname(new_path)
    new_path_prod = os.path.join(dirname, f"prod_{filename}")
    assert os.path.isfile(new_path_prod)
    list_in_prod = assets.list(new_path)
    assert len(list_in_prod) == 1
    histo = list_in_prod.to_dict("records")[0]
    assets.get(new_path, histo.get("timestamp"))
    filename = os.path.basename(new_path)
    dirname = os.path.dirname(new_path)
    new_path_histo = os.path.join(dirname, f"{histo.get('timestamp')}_{filename}")
    assert os.path.isfile(new_path_histo)
    assets.delete(new_path)
    response = await test_runner.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 0
    response = await test_runner.get(f"/{t_asset}/{token}")
    assert response.status == 404


async def test_notebooks(mocker, requests_mock, test_runner, tmp_path):
    test_notebook = "tests/demo/demo_res_json.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    strip_path = os.path.splitdrive(new_path)[1].lstrip(seps)
    real_path = os.path.join(tmp_path, "pytest_tmp", ".naas", strip_path)
    url = api.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    response = await test_runner.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_notebook
    assert res_job.get("path") == real_path
    token = url.split("/")[-1]
    assert res_job.get("value") == token
    assert res_job.get("status") == t_add
    assert res_job.get("nbRun") == 0
    list_in_prod = api.list(new_path)
    assert len(list_in_prod) == 2
    response = await test_runner.get(f"/{t_notebook}/{token}")
    list_out_in_prod = api.list_output(new_path)
    assert len(list_out_in_prod) == 1
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == {"foo": "bar"}
    response = await test_runner.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_notebook
    assert res_job.get("path") == real_path
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
    assert logs.get("totalRecords") == 1
    status = logs.get("data")[0].get("status")
    assert status == "init API"
