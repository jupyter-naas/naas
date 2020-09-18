import pytest
from naas.runner import Runner
import os
import getpass
import shutil

user_folder_name = 'test_user_folder'

@pytest.yield_fixture
def app():
    path_srv_root = os.path.join(os.getcwd(), user_folder_name)
    user = getpass.getuser()

    if os.path.exists(path_srv_root): # TODO remove when test works
        shutil.rmtree(path_srv_root)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    os.environ["JUPYTERHUB_USER"] = user
    os.environ["PUBLIC_PROXY_API"] = 'proxy:5000'
    os.environ["PUBLIC_DATASCIENCE"] = 'localhost:5000'
    
    app = Runner(test_config, **params)
    yield app  

@pytest.fixture
def test_cli(loop, app, sanic_client):
    return loop.run_until_complete(sanic_client(app))

# @pytest.fixture
# def runner():
#     # os.system('test_runner.sh')
#     path_srv_root = os.path.join(os.getcwd(), user_folder_name)
#     user = getpass.getuser()

#     if os.path.exists(path_srv_root): # TODO remove when test works
#         shutil.rmtree(path_srv_root)
#     os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
#     os.environ["JUPYTERHUB_USER"] = user
#     os.environ["PUBLIC_PROXY_API"] = 'proxy:5000'
#     os.environ["PUBLIC_DATASCIENCE"] = 'localhost:5000'
#     # os.environ["NAAS_RUNNER_PORT"] = os.path.join(os.getcwd(), user_folder_name)
#     # os.environ["PUBLIC_DATASCIENCE"] = os.path.join(os.getcwd(), user_folder_name)
#     # os.environ["SINGLEUSER_PATH"] = os.path.join(os.getcwd(), user_folder_name)
#     # os.environ["TZ"] = os.path.join(os.getcwd(), user_folder_name)
#     runner = Runner(testing=True)
#     return runner
#     # TODO add when test work
#     # if os.path.exists(path_srv_root):
#     #     shutil.rmtree(path_srv_root)