from naas.secret import Secret
import pytest
import uuid
import shutil
import os

user_folder_name = 'test_user_folder'

def test_init(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    secret = Secret(clean=True)
    assert os.path.exists(os.path.join(path_srv_root, '.naas'))
    assert len(secret.list()) == 0
    
def test_add(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    secret = Secret(clean=True)
    secret.add('test_1', 'bar')
    assert secret.get('test_1') == 'bar'
    secret.delete('test_1')

def test_keep(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    secret = Secret(clean=True)
    secret.add('test_1', 'bar')
    secret_two = Secret(clean=False)
    assert len(secret_two.list()) == 1
    secret.delete('test_1')

def test_clean(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    secret = Secret(clean=True)
    secret.add('test_1', 'bar')
    secret_two = Secret(clean=True)
    assert len(secret_two.list()) == 0

def test_list(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    secret = Secret(clean=True)
    secret.add('test_1', 'bar')
    assert len(secret.list()) == 1
    secret.delete('test_1')

def test_get(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    secret = Secret(clean=True)
    secret.add('test_1', 'bar')
    assert secret.get('test_1') == 'bar'
    secret.delete('test_1')
    
def test_delete(tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    secret = Secret(clean=True)
    secret.add('test_1', 'bar')
    assert len(secret.list()) == 1
    secret.delete('test_1')
    assert len(secret.list()) == 0
