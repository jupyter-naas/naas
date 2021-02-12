from sanic.views import HTTPMethodView
from sanic.response import json
from naas.types import t_health, t_asset
from naas.runner.env_var import n_env
import uuid

endpoint = "env"


class EnvController(HTTPMethodView):
    __logger = None

    def __init__(
        self,
        logger,
        *args,
        **kwargs
    ):
        super(EnvController, self).__init__(*args, **kwargs)
        self.__logger = logger

    async def get(self, request):
        uid = str(uuid.uuid4())
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
        self.__logger.info(
            {"id": uid, "type": t_asset, "status": "send", "filepath": endpoint}
        )
        return json(env)
