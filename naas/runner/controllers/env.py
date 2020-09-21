from sanic.views import HTTPMethodView
from sanic.response import json
from naas.types import t_health, t_static
import uuid

class EnvController(HTTPMethodView):
    __version = None
    __user = None
    __logger = None
    
    def __init__(self, logger, version, user, public_url, proxy_url, tz, *args, **kwargs):
        super(EnvController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__version = version
        self.__user = user
        self.__public_url = public_url
        self.__proxy_url = proxy_url
        self.__tz = tz

    async def get(self, request):
        uid = str(uuid.uuid4())
        env = {
            'status': t_health,
            'version': self.__version(),
            'JUPYTERHUB_USER': self.__user,
            'JUPYTERHUB_URL': self.__public_url,
            'PUBLIC_PROXY_API': self.__proxy_url,
            'TZ': self.__tz
            
        }
        self.__logger.info(
            {'id': uid, 'type': t_static, 'status': 'send', 'filepath': 'env'})
        return json(env)