from naas.types import t_add, t_delete, t_update
from naas.runner.logger import Logger
from naas.runner.secret import Secret
import pytest  # noqa: F401
import uuid
import os

user_folder_name = "test_user_folder"
clean = True
init_data = []


async def test_init(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    secret = Secret(logger, clean, init_data)
    list_job = await secret.list(uid)
    assert len(list_job) == 0


async def test_add(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    secret = Secret(logger, clean, init_data)
    await secret.update(uid, "test_1", "bar", t_add)
    list_job = await secret.list(uid)
    assert len(list_job) == 1
    data = await secret.find_by_name(uid, "test_1")
    assert data.get("id") == uid
    assert data.get("secret") == "bar"
    await secret.update(uid, "test_1", "", t_delete)
    secret = Secret(logger, clean, init_data)
    list_job = await secret.list(uid)
    assert len(list_job) == 0


async def test_update(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    secret = Secret(logger, clean, init_data)
    await secret.update(uid, "test_1", "bar", t_add)
    list_job = await secret.list(uid)
    assert len(list_job) == 1
    data = await secret.find_by_name(uid, "test_1")
    assert data.get("id") == uid
    assert data.get("secret") == "bar"
    await secret.update(uid, "test_1", "barbar", t_update)
    list_job = await secret.list(uid)
    assert len(list_job) == 1
    data = await secret.find_by_name(uid, "test_1")
    assert data.get("id") == uid
    assert data.get("secret") == "barbar"


async def test_keep(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    secret = Secret(logger, clean, init_data)
    await secret.update(uid, "test_1", "bar", t_add)
    secret_two = Secret(logger, False, [])
    assert len(await secret_two.list(uid)) == 1
    await secret.update(uid, "test_1", "", t_delete)
    secret_tree = Secret(logger, False, [])
    assert len(await secret_tree.list(uid)) == 0


async def test_clean(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    uid = str(uuid.uuid4())
    secret = Secret(logger, clean, init_data)
    await secret.update(uid, "test_1", "bar", t_add)
    secret_two = Secret(logger, clean, init_data)
    assert len(await secret_two.list(uid)) == 0
