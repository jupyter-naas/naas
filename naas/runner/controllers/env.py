from sanic.views import HTTPMethodView
from sanic.response import json
from naas.types import t_health, t_asset
import uuid


class EnvController(HTTPMethodView):
    __notif_url = None
    __user = None
    __logger = None

    def __init__(
        self, logger, user, public_url, proxy_url, notif_url, tz, *args, **kwargs
    ):
        super(EnvController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__notif_url = notif_url
        self.__user = user
        self.__public_url = public_url
        self.__proxy_url = proxy_url
        self.__tz = tz

    async def get(self, request):
        uid = str(uuid.uuid4())
        env = {
            "status": t_health,
            "NOTIFICATIONS_API": self.__notif_url,
            "JUPYTERHUB_USER": self.__user,
            "JUPYTERHUB_URL": self.__public_url,
            "PUBLIC_PROXY_API": self.__proxy_url,
            "TZ": self.__tz,
        }
        self.__logger.info(
            {"id": uid, "type": t_asset, "status": "send", "filepath": "env"}
        )
        return json(env)
