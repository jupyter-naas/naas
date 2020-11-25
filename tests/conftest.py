import pytest  # noqa: F401
import black  # noqa: F401  # FIX for https://github.com/psf/black/issues/1143
import os
import getpass
import logging

user_folder_name = "pytest_tmp"
path_srv_root = os.path.join(os.getcwd(), user_folder_name)
os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
os.environ["NAAS_SCHEDULER_TIME"] = "1"
os.environ["NAAS_SCHEDULER_INSTANCE_MAX"] = "3"
os.environ["JUPYTERHUB_URL"] = "http://localhost:5000"
os.environ["PUBLIC_PROXY_API"] = "http://localhost:5001"
os.environ["NOTIFICATIONS_API"] = "http://localhost:5002"


@pytest.yield_fixture
def runner(caplog, tmp_path):
    caplog.set_level(logging.INFO)
    user = getpass.getuser()
    path_srv_root = os.path.join(tmp_path, user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    os.environ["JUPYTERHUB_USER"] = user

    from naas.runner import Runner  # noqa: E402

    app = Runner().init_app()

    yield app


@pytest.fixture
def test_cli(loop, runner, sanic_client):
    return loop.run_until_complete(sanic_client(runner))
