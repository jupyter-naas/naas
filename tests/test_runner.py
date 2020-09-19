from naas.types import t_health
import pytest
import os
import json
import re
import getpass
from naas.runner import Runner

user_folder_name = 'test_user_folder'
user = getpass.getuser()

os.environ["JUPYTER_SERVER_ROOT"] = os.path.join(os.getcwd(), user_folder_name)
env_data = {'status': 'healthy', 'version': {'error': 'cannot get info.json'}, 'JUPYTERHUB_USER': user, 'PUBLIC_DATASCIENCE': 'localhost:5000', 'PUBLIC_PROXY_API': 'proxy:5000', 'TZ': 'Europe/Paris'}
status_data = {'status': 'running'}
input_headers = [('Content-Type', 'application/json'), ('Accept', 'application/json')]

# @pytest.mark.asyncio
def test_init(runner):
    request, response = runner.test_client.get('/env')
    assert response.status == 200
    assert env_data == response.json
    
def test_sheduler(runner):
    request, response = runner.test_client.get('/scheduler/status')
    assert response.status == 200
    assert status_data == response.json

def test_static(runner):
    request, response = runner.test_client.get('/static/up')
    assert response.status == 200
    # TODO add more test

def test_logs(runner):
    request, response = runner.test_client.get('/logs')
    assert response.status == 200
    logs = response.json
    assert logs.get('totalRecords') == 1
    status = logs.get('data')[0].get('status')
    assert status == 'start API'