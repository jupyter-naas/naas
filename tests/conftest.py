import pytest
from naas import Runner
import os
import getpass

user_folder_name = 'test_user_folder'

@pytest.fixture(scope="session")
def runner():
    # os.system('test_runner.sh')
    path_srv_root = os.path.join(os.getcwd(), user_folder_name)
    user = getpass.getuser()

    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    os.environ["JUPYTERHUB_USER"] = user
    os.environ["PUBLIC_PROXY_API"] = 'proxy:5000'
    os.environ["PUBLIC_DATASCIENCE"] = 'localhost:5000'
    # os.environ["NAAS_RUNNER_PORT"] = os.path.join(os.getcwd(), user_folder_name)
    # os.environ["PUBLIC_DATASCIENCE"] = os.path.join(os.getcwd(), user_folder_name)
    # os.environ["SINGLEUSER_PATH"] = os.path.join(os.getcwd(), user_folder_name)
    # os.environ["TZ"] = os.path.join(os.getcwd(), user_folder_name)
    # runner = Runner(path=path_srv_root, port=5000, user=user, public='localhost:5000', proxy='proxy:5000', testing=True)
    runner = Runner(testing=True)
    runner.register(runner.get_app())
    return runner
