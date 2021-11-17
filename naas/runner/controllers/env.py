from sanic.views import HTTPMethodView
from sanic.response import json
from naas.ntypes import t_health
from naas.runner.env_var import n_env
import requests


def get_latest_version():
    try:
        r = requests.get("https://pypi.python.org/pypi/naas/json")
        r.raise_for_status()
        response = r.json()
        version = (
            response["urls"][0]["filename"].replace("naas-", "").replace(".tar.gz", "")
        )
        return version
    except:  # noqa: E722
        return ""


class EnvController(HTTPMethodView):
    def __init__(self, *args, **kwargs):
        super(EnvController, self).__init__(*args, **kwargs)

    async def get(self, request):

        env = {
            "status": t_health,
            "version": n_env.version,
            "latest_version": get_latest_version(),
            "NAAS_BASE_PATH": n_env.path_naas_folder,
            "NOTIFICATIONS_API": n_env.notif_api,
            "JUPYTERHUB_USER": n_env.user,
            "JUPYTER_SERVER_ROOT": n_env.server_root,
            "JUPYTERHUB_URL": n_env.hub_base,
            "PUBLIC_PROXY_API": n_env.proxy_api,
            "TZ": n_env.tz,
        }
        return json(env)
