from naas.types import t_health, t_add
from naas.runner import Runner
import getpass
import logging
import pytest
import json
import uuid
import os

user_folder_name = 'test_user_folder'
user = getpass.getuser()

os.environ["JUPYTER_SERVER_ROOT"] = os.path.join(os.getcwd(), user_folder_name)
env_data = {'status': 'healthy', 'version': {'error': 'cannot get info.json'}, 'JUPYTERHUB_USER': user, 'JUPYTERHUB_URL': 'localhost:5000', 'PUBLIC_PROXY_API': 'proxy:5000', 'TZ': 'Europe/Paris'}
status_data = {'status': 'running'}
input_headers = [('Content-Type', 'application/json'), ('Accept', 'application/json')]

# @pytest.mark.asyncio
def test_init(runner):
    request, response = runner.test_client.get('/env')
    assert response.status == 200
    assert response.json == env_data
    
def test_sheduler(runner):
    request, response = runner.test_client.get('/scheduler/status')
    assert response.status == 200
    assert response.json == status_data

def test_static(runner):
    request, response = runner.test_client.get('/static/up')
    assert response.status == 200
    # TODO add more test

def test_notebooks(runner):
    path = os.path.join(os.getcwd(), 'tests/demo_json_res.ipynb')
    token = str(uuid.uuid4())
    job = {"type": "api", "path": path, "params": {}, "value": token, "status": "installed"}
    request, response = runner.test_client.post('/jobs', data=json.dumps(job))
    assert response.status == 200
    request, response = runner.test_client.get('/jobs')
    assert response.status == 200
    assert len(response.json) == 1
    res_job = response.json[0]
    assert res_job.get('path') == path
    assert res_job.get('value') == token
    assert res_job.get('status') == t_add
    # TODO fix testing run notebook
    # request, response = runner.test_client.get(f'/notebooks/{token}')
    # assert response.status == 200
    # assert response.json == {'foo': 'bar'}
    # request, response = runner.test_client.get('/jobs')
    # assert response.status == 200
    # assert len(response.json) == 1
    # res_job = response.json[0]
    # assert res_job.get('path') == path
    # assert res_job.get('value') == token
    # assert res_job.get('status') == t_health
    
    
def test_logs(runner):
    request, response = runner.test_client.get('/logs')
    assert response.status == 200
    logs = response.json
    assert logs.get('totalRecords') == 2
    status = logs.get('data')[0].get('status')
    assert status == 'init API'