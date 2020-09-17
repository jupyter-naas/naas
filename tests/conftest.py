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
    runner = Runner(path=path_srv_root, port=5000, user=user, public='localhost:5000', proxy='proxy:5000', testing=True)
    return runner
