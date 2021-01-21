from naas.types import t_add, t_health, t_scheduler, t_job
from naas.runner.logger import Logger
from naas.runner.jobs import Jobs
from naas.runner.scheduler import Scheduler
from naas.runner.notebooks import Notebooks
from naas import scheduler
import getpass
import pytest  # noqa: F401
import uuid
import os
from shutil import copy2
from datetime import datetime, timedelta
from naas.runner import n_env
from syncer import sync

user_folder_name = "test_user_folder"
user = getpass.getuser()

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


async def test_scheduler_status(test_scheduler):
    response = await test_scheduler.get("/scheduler/status")
    assert response.status == 200
    resp_json = await response.json()
    assert resp_json == status_data


async def test_scheduler(tmp_path, event_loop):
    recur = "* * * * *"
    test_notebook = "tests/demo/demo_scheduler.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    logger = Logger()
    notebooks = Notebooks(logger)
    jobs = Jobs(logger, True, [])
    scheduler = Scheduler(logger, jobs, notebooks, event_loop)
    uid = str(uuid.uuid4())
    copy2(cur_path, new_path)
    job = {
        "type": t_scheduler,
        "path": new_path,
        "params": {},
        "value": recur,
        "status": t_add,
    }
    await jobs.update(
        uid,
        job["path"],
        job["type"],
        job["value"],
        job["params"],
        job["status"],
    )
    resp_json = await jobs.list(uid)
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_add
    await scheduler.start(test_mode=True)
    resp_json = await jobs.list(uid)
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_health
    # TODO add more tests


async def test_scheduler_runner(mocker, requests_mock, test_scheduler, tmp_path):
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
