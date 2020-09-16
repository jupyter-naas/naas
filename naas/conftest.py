import pytest
from .runner import Runner
import os
import getpass

@pytest.fixture(scope="session")
def runner():
    # os.system('test_runner.sh')
    path_srv_root = os.path.join(os.getcwd(), 'test')
    user = getpass.getuser()
    runner = Runner(path=path_srv_root, port=5000, user=user, public='localhost:5000', proxy='proxy:5000')
    runner.start(deamon=False)
    return runner