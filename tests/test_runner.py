from naas.types import t_health
import pytest
import os
import json
import re

user_folder_name = 'test_user_folder'

os.environ["JUPYTER_SERVER_ROOT"] = os.path.join(os.getcwd(), user_folder_name)

def test_init(runner):
    with runner.get_app().app_context():
        req = runner.env()
        env = json.loads(req[0].data)
        assert env == {'JUPYTERHUB_USER': 'martindonadieu', 'PUBLIC_DATASCIENCE': 'localhost:5000', 'PUBLIC_PROXY_API': 'proxy:5000', 'TZ': 'Europe/Paris'}
        req = runner.index()
        env = json.loads(req[0].data)
        assert env == {'status': t_health}
        c =  runner.get_app().test_client()
        req =  c.get('/v1/')
        assert req.status_code == 200
        assert req[0] == {'status': t_health}
        

def test_logs(runner):
    with runner.get_app().app_context():
        req = runner.logs()
        logs = json.loads(req[0].data)
        assert logs == {}