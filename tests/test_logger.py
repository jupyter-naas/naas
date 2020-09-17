from naas.types import t_add, t_delete, t_update
from naas.logger import Logger
import pytest
import uuid
import json
import os

user_folder_name = 'test_user_folder'

def test_init(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    data = logger.list(uid).get('data')
    assert len(data) == 1
    log = data[0]
    assert log['levelname'] == 'INFO'
    assert log['funcName'] == '__init__'
    logger.clear()

def test_no_clean(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    assert len(logger.list(uid).get('data')) == 1
    logger.write.info(json.dumps({'id': uid, 'type': t_add, "status": 'test_1'}))
    logger_new = Logger()
    assert len(logger_new.list(uid).get('data')) == 2
    logger_new.clear()
    

def test_add(tmp_path, caplog):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    # print('logs', list(logger.list(uid).get('data')))
    data = {'id': uid, 'type': t_add, "status": 'test_2'}
    logger.write.info(json.dumps(data))
    all_logs = logger.list(uid).get('data')
    print('all_logs', all_logs)
    assert len(all_logs) == 2
    log = all_logs[1]
    assert log['levelname'] == 'INFO'
    assert log['funcName'] == 'test_add'
    assert log['id'] == uid
    assert log['type'] == t_add
    assert log['status'] == 'test_2'

def test_list(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    data = {'id': uid, 'type': t_add, "status": 'test_1'}
    data_two = {'id': uid, 'type': t_delete, "status": 'test_2'}
    data_tree = {'id': uid, 'type': t_update, "status": 'test_2'}
    logger.write.info(json.dumps(data))
    logger.write.info(json.dumps(data_two))
    logger.write.info(json.dumps(data_tree))
    all_logs = logger.list(uid).get('data')
    assert len(all_logs) == 4
    assert len(logger.list(uid, skip = 1).get('data')) == 3
    assert len(logger.list(uid, skip = 0, limit = 1).get('data')) == 1
    assert len(logger.list(uid, skip = 1, limit = 1).get('data')) == 1
    assert len(logger.list(uid, skip = 0, limit = 0, search = 'test_2').get('data')) == 2
    assert len(logger.list(uid, skip = 0, limit = 0, search = 'test_2').get('data')) == 2
    assert len(logger.list(uid, skip = 0, limit = 0, search = None, filters=[t_delete, t_add]).get('data')) == 3