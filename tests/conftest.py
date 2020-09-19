import pytest
from naas.runner import Runner
import os
import getpass
import shutil
import logging

user_folder_name = 'test_user_folder'

@pytest.yield_fixture
# @pytest.fixture
def runner(caplog):
    caplog.set_level(logging.INFO)
    path_srv_root = os.path.join(os.getcwd(), user_folder_name)
    user = getpass.getuser()

    if os.path.exists(path_srv_root): # TODO remove when test works
        shutil.rmtree(path_srv_root)
    os.environ["JUPYTER_SERVER_ROOT"] = path_srv_root
    os.environ["JUPYTERHUB_USER"] = user
    os.environ["PUBLIC_PROXY_API"] = 'proxy:5000'
    os.environ["PUBLIC_DATASCIENCE"] = 'localhost:5000'
    
    app = Runner().init_app()
    
    yield app  
    # yield app  
    # yield app.asgi_client  
#     # TODO add when test work
#     # if os.path.exists(path_srv_root):
#     #     shutil.rmtree(path_srv_root)

# @pytest.fixture
# def runner(app):
#     return app.asgi_client

# @pytest.fixture
# def test_cli(loop, app, test_client):
#     return loop.run_until_complete(test_client(app, protocol=WebSocketProtocol))
