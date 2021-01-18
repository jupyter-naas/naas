import pytest  # noqa: F401
import os
import getpass
import logging
from naas.runner import Runner, n_env

os.environ["SANIC_REGISTER"] = "False"
user_folder_name = "pytest_tmp"
path_srv_root = os.path.join(os.getcwd(), user_folder_name)
n_env.server_root = str(path_srv_root)


@pytest.fixture
def runner(caplog, tmp_path):
    caplog.set_level(logging.INFO)
    user = getpass.getuser()
    path_srv = os.path.join(tmp_path, user_folder_name)
    n_env.user = user
    n_env.server_root = str(path_srv)
    n_env.scheduler = False
    n_env.hub_api = "http://localhost:5000"
    n_env.proxy_api = "http://localhost:5001"
    n_env.notif_api = "http://localhost:5002"

    app = Runner().init_app()

    yield app
    app.stop()


@pytest.fixture
def scheduler(caplog, tmp_path):
    caplog.set_level(logging.INFO)
    user = getpass.getuser()
    path_srv = os.path.join(tmp_path, user_folder_name)
    n_env.user = user
    n_env.server_root = str(path_srv)
    n_env.scheduler = True
    n_env.scheduler_interval = "1"
    n_env.scheduler_job_max = "3"
    n_env.hub_api = "http://localhost:5000"
    n_env.proxy_api = "http://localhost:5001"
    n_env.notif_api = "http://localhost:5002"

    app = Runner().init_app()

    yield app
    app.stop()


@pytest.fixture
def test_runner(loop, runner, sanic_client):
    return loop.run_until_complete(sanic_client(runner))


@pytest.fixture
def test_scheduler(loop, scheduler, sanic_client):
    return loop.run_until_complete(sanic_client(scheduler))
