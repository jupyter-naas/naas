from naas.types import t_health
import pytest
import os
import json
import re
import getpass

user_folder_name = 'test_user_folder'
user = getpass.getuser()

os.environ["JUPYTER_SERVER_ROOT"] = os.path.join(os.getcwd(), user_folder_name)
env_data = {'status': 'healthy', 'version': {'error': 'cannot get info.json'}, 'JUPYTERHUB_USER': user, 'PUBLIC_DATASCIENCE': 'localhost:5000', 'PUBLIC_PROXY_API': 'proxy:5000', 'TZ': 'Europe/Paris'}
status_data = {'status': 'running'}
input_headers = [('Content-Type', 'application/json'), ('Accept', 'application/json')]

def test_init(runner):
    app = runner.get_test()
    # with app.app_context() and app.test_client() as c:
    req = app.get('/v1/env', headers=input_headers)
    assert req.status_code == 200
    env = json.loads(req.data)
    assert env == env_data

def test_sheduler(runner):
    app = runner.get_test()
    # with app.app_context() and app.test_client() as c:
    req = app.get('/v1/scheduler/status', headers=input_headers)
    assert req.status_code == 200
    scheduler_status = json.loads(req.data)
    assert status_data == scheduler_status     

def test_logs(runner):
    app = runner.get_test()
    req = app.get('/v1/logs', headers=input_headers)
    assert req.status_code == 200
    logs = json.loads(req.data)
    assert logs.get('totalRecords') == 1
    status = logs.get('data')[0].get('status')
    assert status == 'start API'