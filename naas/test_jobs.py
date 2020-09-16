from .types import t_notebook, t_add, t_delete, t_update
from .jobs import Jobs
from .logger import Logger
import shutil
import pytest
import uuid
import os

clean = True
init_data = []

def test_init(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), 'test')
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    logger = Logger()
    path_nass = os.path.join(path_srv_root, '.naas', 'jobs.json')
    uid = str(uuid.uuid4())
    jobs = Jobs(uid, logger, clean, init_data)
    assert len(jobs.list(uid)) == 0

def test_add(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), 'test')
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(uid, logger, clean, init_data)
    path =  os.path.join(os.getcwd(), 'test_add.py')
    target_type = t_notebook
    value = 'test'
    params = {}
    runTime = 0
    jobs.update(uid, path, target_type, value, params, t_add, runTime)
    assert len(jobs.list(uid)) == 1
    data = jobs.find_by_path(uid, path, target_type)
    assert data.get('value') == value
    assert data['params'] == params
    assert data['lastRun'] == runTime
    jobs.update(uid, path, target_type, value, params, t_delete, runTime)

def test_clean_data(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), 'test')
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(uid, logger, clean, init_data)
    path =  os.path.join(os.getcwd(), 'test_add.py')
    target_type = t_notebook
    value = 'test'
    params = {}
    runTime = 0
    jobs.update(uid, path, target_type, value, params, t_add, runTime)
    assert len(jobs.list(uid)) == 1
    jobs = Jobs(uid, logger, clean, init_data)
    assert len(jobs.list(uid)) == 0

def test_delete(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), 'test')
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(uid, logger, clean, init_data)
    path =  os.path.join(os.getcwd(), 'test_delete.py')
    target_type = t_notebook
    value = 'test'
    params = {}
    runTime = 0
    jobs.update(uid, path, target_type, value, params, t_add, runTime)
    assert len(jobs.list(uid)) == 1
    jobs.update(uid, path, target_type, value, params, t_delete, runTime)
    assert len(jobs.list(uid)) == 0

def test_update(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), 'test')
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    logger = Logger()
    uid = str(uuid.uuid4())
    jobs = Jobs(uid, logger, clean, init_data)
    path =  os.path.join(os.getcwd(), 'test_update.py')
    target_type = t_notebook
    value = 'test'
    new_value = 'value_changed'
    params = {}
    runTime = 0
    jobs.update(uid, path, target_type, value, params, t_add, runTime)
    assert len(jobs.list(uid)) == 1
    jobs.update(uid, path, target_type, new_value, params, t_update, runTime)
    assert len(jobs.list(uid)) == 1
    data = jobs.find_by_path(uid, path, target_type)
    assert data['value'] == new_value
    jobs.update(uid, path, target_type, value, params, t_delete, runTime)
    assert len(jobs.list(uid)) == 0