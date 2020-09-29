import pytest  # noqa: F401
import os
import getpass
import logging

user_folder_name = "test_user_folder"
path_srv_root = os.path.join(os.getcwd(), user_folder_name)
os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)


@pytest.fixture
def runner(caplog, tmp_path):
    caplog.set_level(logging.INFO)
    user = getpass.getuser()
    path_srv_root = os.path.join(tmp_path, user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    os.environ["JUPYTERHUB_USER"] = user
    os.environ["JUPYTERHUB_URL"] = "localhost:5000"
    os.environ["PUBLIC_PROXY_API"] = "localhost:5001"
    os.environ["NOTIFICATIONS_API"] = "localhost:5002"

    from naas.runner import Runner  # noqa: E402

    app = Runner().init_app()

    yield app
