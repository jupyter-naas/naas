from sanic.views import HTTPMethodView
from sanic.response import json
from naas.types import t_health
from naas.runner.env_var import n_env


class EnvController(HTTPMethodView):
    def __init__(self, *args, **kwargs):
        super(EnvController, self).__init__(*args, **kwargs)

    async def get(self, request):
        env = {
            "status": t_health,
            "version": n_env.version,
            "NAAS_BASE_PATH": n_env.path_naas_folder,
            "NOTIFICATIONS_API": n_env.notif_api,
            "JUPYTERHUB_USER": n_env.user,
            "JUPYTER_SERVER_ROOT": n_env.server_root,
            "JUPYTERHUB_URL": n_env.hub_api,
            "PUBLIC_PROXY_API": n_env.proxy_api,
            "TZ": n_env.tz,
        }
        return json(env)
