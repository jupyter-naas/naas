from naas.ntypes import t_notebook
from naas.manager import Manager
from naas.runner import n_env
import pytest  # noqa: F401
import os
import json

user_folder_name = "test_user_folder"
test_demo_folder = "demo"
test_file = "demo_file.py"
token = "test_token"
test_file_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), test_demo_folder, test_file
)
n_env.hub_base = "https://test.naas.com"
n_env.user = "TEST_USER"
n_env.token = "TESTAPIKEY"
n_env.proxy_api = "proxy.naas.com"


def mock_for_nb_path(mocker, requests_mock):
    mocker.patch(
        "ipykernel.get_connection_file",
        return_value="kernel-b1e19209-e251-4115-819e-7ab5bc4232b7.json",
    )
    mock_json = json.loads(open("tests/session_ids.json").read())
    url = f"{n_env.user_url}/api/sessions"
    requests_mock.register_uri("GET", url, json=mock_json, status_code=200)


def test_nb_path(mocker, requests_mock, tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    n_env.server_root = path_srv_root
    mock_for_nb_path(mocker, requests_mock)
    manager = Manager(t_notebook)
    assert manager.notebook_path() == os.path.join(
        path_srv_root, "MAIN_DIR/TEST_DIR1/ANOTHER_DIR1"
    )


def test_get_path(mocker, requests_mock, tmp_path):
    path_srv_root = os.path.join(str(tmp_path), user_folder_name)
    n_env.server_root = path_srv_root
    mock_for_nb_path(mocker, requests_mock)
    manager = Manager(t_notebook)
    assert manager.notebook_path() == os.path.join(
        path_srv_root, "MAIN_DIR/TEST_DIR1/ANOTHER_DIR1"
    )
    assert manager.get_path(test_file_path) == test_file_path


# TODO test all other functions

# def get_naas(self):

# def get_value(self, path, obj_type):

# def is_already_use(self, obj):

# def get_prod(self, path):

# def get_output(self, path):

# def clear_output(self, path):

# def list_history(self, path):

# def get_history(self, path, histo):

# def clear_history(self, path, histo=None):

# def add_prod(self, obj, silent):

# def del_prod(self, obj, silent):
