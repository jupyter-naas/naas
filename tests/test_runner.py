from base64 import b64encode
from naas.runner.proxy import escape_kubernet
from naas.types import (
    t_add,
    t_notebook,
    t_job,
    t_health,
    t_asset,
    t_secret,
    t_output,
)
import getpass
import pytest  # noqa: F401
import os
from shutil import copy2
from naas.runner import n_env
from naas import assets, webhook, secret
from nbconvert import HTMLExporter
from syncer import sync
import pandas as pd
import csv
import markdown2

# import imgcompare
# from PIL import Image
# import io

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
    new_path_histo = os.path.join(dirname, f"{histo.get('timestamp')}___{filename}")
    assert os.path.isfile(new_path_histo)
    url_new = assets.add(new_path)
    assert url == url_new
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
    url = webhook.add(new_path)
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
    list_in_prod = webhook.list(new_path)
    assert len(list_in_prod) == 1
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    resp_json = await response.json()
    assert response.headers.get("Content-Disposition") is not None
    assert resp_json == {"foo": "bar"}
    list_out_in_prod = webhook.list_output(new_path)
    assert len(list_out_in_prod) == 1
    histo = list_out_in_prod.to_dict("records")[0]
    webhook.get_output(new_path, histo.get("timestamp"))
    filename = os.path.basename(new_path)
    dirname = os.path.dirname(new_path)
    new_path_out_histo = os.path.join(
        dirname, f"{histo.get('timestamp')}___{t_output}__{filename}"
    )
    assert os.path.isfile(new_path_out_histo)
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
    webhook.delete(new_path)
    response = await test_runner.get(f"/{t_job}")
    assert response.status == 200
    resp_json = await response.json()
    assert len(resp_json) == 0
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 404


async def test_notebooks_res(mocker, requests_mock, test_runner, tmp_path):
    # test json
    test_notebook = "tests/demo/demo_res_json.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path, params={"inline": True})
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "application/json"
    assert response.headers.get("Content-Disposition") is None
    resp_json = await response.json()
    assert resp_json == {"foo": "bar"}
    # test csv
    test_notebook = "tests/demo/demo_res_csv.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "text/csv"
    res_text = await response.content.read()
    res_text = res_text.decode("utf-8")
    empoyees = [
        (
            "jack",
            34,
            "Sydney",
            5,
            111,
            112,
            134,
            122,
            445,
            122,
            111,
            15,
            111,
            112,
            134,
            122,
            1445,
            122,
            111,
            15,
            111,
            112,
            134,
            122,
            445,
            122,
            111,
        ),
        (
            "Riti",
            31,
            "Delhia",
            27,
            211,
            212,
            234,
            222,
            2445,
            222,
            211,
            25,
            211,
            212,
            234,
            222,
            2445,
            222,
            211,
            25,
            211,
            212,
            234,
            222,
            2445,
            222,
            211,
        ),
        (
            "Aadi",
            16,
            "Tokyo",
            39,
            311,
            312,
            334,
            322,
            3445,
            322,
            311,
            35,
            311,
            312,
            334,
            322,
            3445,
            322,
            311,
            35,
            311,
            312,
            334,
            322,
            3445,
            322,
            311,
        ),
        (
            "Sunil",
            41,
            "Delhi",
            412,
            411,
            412,
            434,
            422,
            4445,
            422,
            411,
            45,
            411,
            412,
            434,
            422,
            4445,
            422,
            411,
            45,
            411,
            412,
            434,
            422,
            4445,
            422,
            411,
        ),
        (
            "Veena",
            33,
            "Delhi",
            54,
            511,
            512,
            534,
            522,
            5445,
            522,
            511,
            55,
            511,
            512,
            534,
            522,
            5445,
            522,
            511,
            55,
            511,
            512,
            534,
            522,
            5445,
            522,
            511,
        ),
        (
            "Shaunak",
            35,
            "Mumbai",
            665,
            611,
            612,
            634,
            622,
            6445,
            622,
            611,
            65,
            611,
            612,
            634,
            622,
            6445,
            622,
            611,
            65,
            611,
            612,
            634,
            622,
            6445,
            622,
            611,
        ),
        (
            "Shaun",
            35,
            "Colombo",
            711,
            711,
            712,
            734,
            722,
            7445,
            722,
            711,
            75,
            711,
            712,
            734,
            722,
            7445,
            722,
            711,
            75,
            711,
            712,
            734,
            722,
            7445,
            722,
            711,
        ),
    ]
    empDfObj = pd.DataFrame(
        empoyees,
        columns=[
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
            "AA",
        ],
    )
    empDfObj = empDfObj.append([empDfObj] * 8, ignore_index=True)
    csv_text = empDfObj.to_csv(sep=";", quoting=csv.QUOTE_ALL)
    assert res_text == csv_text
    # test notebook
    test_notebook = "tests/demo/demo_res_nb.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "text/html"
    res_text = await response.content.read()
    res_text = res_text.decode("utf-8")
    html_exporter = HTMLExporter()
    html_exporter.template_name = "lab"
    strip_path = os.path.splitdrive(new_path)[1].lstrip(seps)
    real_path = os.path.join(tmp_path, "pytest_tmp", ".naas", strip_path)
    filename = os.path.basename(real_path)
    dirname = os.path.dirname(real_path)
    new_path_out = os.path.join(dirname, f"{t_output}__{filename}")
    (result, ressources) = html_exporter.from_filename(new_path_out)
    assert res_text == result
    # test html
    test_notebook = "tests/demo/demo_res_html.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "text/html"
    res_text = await response.content.read()
    res_text = res_text.decode("utf-8")
    demo_html = open("tests/demo/demo.html")
    html_text = demo_html.read()
    assert res_text == html_text
    # test markdown
    test_notebook = "tests/demo/demo_res_md.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "text/html"
    res_text = await response.content.read()
    res_text = res_text.decode("utf-8")
    demo_html = open("tests/demo/demo.md")
    md_text = demo_html.read()
    html_text = markdown2.markdown(md_text)
    assert res_text == html_text
    # test text
    test_notebook = "tests/demo/demo_res_text.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "text/html"
    res_text = await response.content.read()
    res_text = res_text.decode("utf-8")
    demo_html = open("tests/demo/demo.md")
    md_text = demo_html.read()
    assert res_text == md_text
    # test file
    test_notebook = "tests/demo/demo_res_file.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "text/csv"
    res_text = await response.content.read()
    csv_val = open("tests/demo/PEIX.csv", "rb").read()
    assert res_text == csv_val
    # test SVG
    test_notebook = "tests/demo/demo_res_svg.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    copy2(cur_path, new_path)
    mock_session(mocker, requests_mock, new_path)
    mock_job(requests_mock, test_runner)
    url = webhook.add(new_path)
    assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    token = url.split("/")[-1]
    response = await test_runner.get(f"/{t_notebook}/{token}")
    assert response.status == 200
    assert response.headers.get("Content-Type") == "image/svg+xml"
    res_text = await response.content.read()
    csv_val = open("tests/demo/demo.svg", "rb").read()
    assert res_text == csv_val
    # test image
    # test_notebook = "tests/demo/demo_res_image.ipynb"
    # cur_path = os.path.join(os.getcwd(), test_notebook)
    # new_path = os.path.join(tmp_path, test_notebook)
    # copy2(cur_path, new_path)
    # mock_session(mocker, requests_mock, new_path)
    # mock_job(requests_mock, test_runner)
    # url = webhook.add(new_path)
    # assert url.startswith(f"http://localhost:5001/{getUserb64()}/notebook/")
    # token = url.split("/")[-1]
    # response = await test_runner.get(f"/{t_notebook}/{token}")
    # assert response.status == 200
    # assert response.headers.get("Content-Type") == "image/jpeg"
    # res_text = await response.content.read()
    # image_a = Image.open('tests/demo/dog.jpeg')
    # image_b = Image.open(io.BytesIO(res_text))
    # percentage = imgcompare.image_diff_percent(image_a, image_b)
    # assert percentage < 1


async def test_logs(test_runner):
    response = await test_runner.get("/log")
    assert response.status == 200
    logs = await response.json()
    assert logs.get("totalRecords") == 1
    status = logs.get("data")[0].get("status")
    assert status == "init API"
