from sanic.views import HTTPMethodView
from naas_drivers import naasauth
from sanic.response import json
import os

TOKEN = os.environ.get("PROD_JUPYTERHUB_API_TOKEN", None)


class AuthController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(AuthController, self).__init__(*args, **kwargs)
        self.__logger = logger

    class UserController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(AuthController.UserController, self).__init__(*args, **kwargs)
            self.__logger = logger

        async def get(self, request):
            res = naasauth.connect(TOKEN).user.me()
            return json(res)
