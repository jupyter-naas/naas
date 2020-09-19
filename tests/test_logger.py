from naas.types import t_add, t_delete, t_update
from naas.runner.logger import Logger
import pytest
import logging
import uuid
import os

user_folder_name = 'test_user_folder'

def test_init(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    path_srv_root = os.path.join(os.getcwd(), user_folder_name)
    # path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger(clear=True)
    uid = str(uuid.uuid4())
    data = logger.list(uid).get('data')
    assert len(data) == 0
    logger.info({'id': uid, 'status': 'inited', 'type': t_add})
    data = logger.list(uid).get('data')
    assert len(data) == 1
    log = data[0]
    assert log['levelname'] == 'INFO'
    assert log['status'] == 'inited'
    assert log['id'] == uid

def test_clean(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger(clear=True)
    uid = str(uuid.uuid4())
    data = logger.list(uid).get('data')
    assert len(data) == 0
    logger.info({'id': uid, 'type': t_add, "status": 'test_1'})
    data = logger.list(uid).get('data')
    assert len(data) == 1
    logger_new = Logger()
    assert len(logger_new.list(uid).get('data')) == 1
    logger_new.clear()
    assert len(logger_new.list(uid).get('data')) == 0
    

def test_add(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    # print('logs', list(logger.list(uid).get('data')))
    data = {'id': uid, 'type': t_add, "status": 'test_2'}
    logger.info(data)
    all_logs = logger.list(uid).get('data')
    print('all_logs', all_logs)
    assert len(all_logs) == 1
    log = all_logs[0]
    assert log['levelname'] == 'INFO'
    assert log['id'] == uid
    assert log['type'] == t_add
    assert log['status'] == 'test_2'

def test_list(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    data = {'id': uid, 'type': t_add, "status": 'test_1'}
    data_two = {'id': uid, 'type': t_delete, "status": 'test_2'}
    data_tree = {'id': uid, 'type': t_update, "status": 'test_2'}
    logger.info(data)
    logger.info(data_two)
    logger.info(data_tree)
    all_logs = logger.list(uid).get('data')
    assert len(all_logs) == 3
    assert len(logger.list(uid, skip = 1).get('data')) == 2
    assert len(logger.list(uid, skip = 0, limit = 1).get('data')) == 1
    assert len(logger.list(uid, skip = 1, limit = 1).get('data')) == 1
    assert len(logger.list(uid, skip = 0, limit = 0, search = 'test_2').get('data')) == 2
    assert len(logger.list(uid, skip = 0, limit = 0, search = 'test_2').get('data')) == 2
    assert len(logger.list(uid, skip = 0, limit = 0, search = None, filters=[t_delete, t_add]).get('data')) == 2