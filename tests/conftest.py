import pytest  # noqa: F401
import os
import getpass
import shutil
import logging

user_folder_name = "test_user_folder"
path_srv_root = os.path.join(os.getcwd(), user_folder_name)
os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
from naas.runner import Runner  # noqa: E402


@pytest.fixture
def runner(caplog):
    caplog.set_level(logging.INFO)
    path_srv_root = os.path.join(os.getcwd(), user_folder_name)
    user = getpass.getuser()
    os.environ["JUPYTERHUB_USER"] = user
    os.environ["JUPYTERHUB_URL"] = "localhost:5000"
    os.environ["PUBLIC_PROXY_API"] = "localhost:5001"
    os.environ["NOTIFICATIONS_API"] = "localhost:5002"

    if os.path.exists(path_srv_root):
        shutil.rmtree(path_srv_root)

    app = Runner().init_app()

    yield app
    if os.path.exists(path_srv_root):
        shutil.rmtree(path_srv_root)
