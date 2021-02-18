from naas.types import t_notebook, t_add, t_delete, t_update
from naas.runner.jobs import Jobs
from naas.runner.logger import Logger
from naas.runner import n_env
import pytest  # noqa: F401
import json
import uuid
import os

clean = True
init_data = []

user_folder_name = "test_user_folder"
test_file = "test_add.py"

wrong_jobs_list = [
    {
        "id": "7450272a-0933-4be0-8c67-97de83fbe92a",
        "lastRun": 0,
        "lastUpdate": "2021-02-17 12:32:58",
        "nbRun": 0,
        "params": {},
        "path": "/home/ftp/.naas/home/ftp/sales/contacts/output/REF_HUBSPOT_CONTACTS.csv",
        "status": "installed",
        "totalRun": 0,
        "type": "asset",
        "value": "f47887a7d8da171e617f800e5d71c022f4923a42758f814399d45aab7427"
    },
]


async def test_init(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(logger, clean, init_data)
    list_job = await jobs.list(uid)
    assert len(list_job) == 0


async def test_add(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(logger, clean, init_data)
    path = os.path.join(os.getcwd(), test_file)
    target_type = t_notebook
    value = user_folder_name
    params = {}
    run_time = 0
    await jobs.update(uid, path, target_type, value, params, t_add, run_time)
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    data = await jobs.find_by_path(uid, path, target_type)
    assert data.get("value") == value
    assert data["params"] == params
    assert data["lastRun"] == run_time
    jobs = Jobs(logger, clean, init_data)
    list_job = await jobs.list(uid)
    assert len(list_job) == 0


async def test_delete(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(logger, clean, init_data)
    path = os.path.join(os.getcwd(), "test_delete.py")
    target_type = t_notebook
    value = user_folder_name
    params = {}
    run_time = 0
    await jobs.update(uid, path, target_type, value, params, t_add, run_time)
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    await jobs.update(uid, path, target_type, value, params, t_delete, run_time)
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    assert list_job[0].get("status") == t_delete


async def test_keep(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(logger, clean, init_data)
    path = os.path.join(os.getcwd(), test_file)
    target_type = t_notebook
    value = user_folder_name
    params = {}
    run_time = 0
    await jobs.update(uid, path, target_type, value, params, t_add, run_time)
    jobs_two = Jobs(logger, False, [])
    assert len(await jobs_two.list(uid)) == 1
    await jobs.update(uid, path, target_type, value, params, t_delete, run_time)
    Jobs(logger, False, [])
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    assert list_job[0].get("status") == t_delete


async def test_clean(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(logger, clean, init_data)
    path = os.path.join(os.getcwd(), test_file)
    target_type = t_notebook
    value = user_folder_name
    params = {}
    run_time = 0
    await jobs.update(uid, path, target_type, value, params, t_add, run_time)
    jobs_two = Jobs(logger, clean, init_data)
    assert len(await jobs_two.list(uid)) == 0


async def test_update(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(logger, clean, init_data)
    path = os.path.join(os.getcwd(), "test_update.py")
    target_type = t_notebook
    value = user_folder_name
    new_value = "value_changed"
    params = {}
    run_time = 0
    await jobs.update(uid, path, target_type, value, params, t_add, run_time)
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    await jobs.update(uid, path, target_type, new_value, params, t_update, run_time)
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    data = await jobs.find_by_path(uid, path, target_type)
    assert data["value"] == new_value
    assert data["status"] == t_update
    await jobs.update(uid, path, target_type, value, params, t_delete, run_time)
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    assert list_job[0].get("status") == t_delete


async def test_migration(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    with open(os.path.join(n_env.path_naas_folder, "jobs.json"), "w+") as f:
        f.write(os.path.join(json.dumps(wrong_jobs_list)))
    jobs = Jobs(logger, False, init_data)
    list_job = await jobs.list(uid)
    assert len(list_job) == 1
    assert list_job[0].get("runs") == []
    assert list_job[0].get("nbRun") is None
    assert list_job[0].get("totalRun") is None
