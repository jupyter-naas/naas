from sanic.views import HTTPMethodView
import json
import requests
from naas.runner.env_var import n_env


class VersionController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(VersionController, self).__init__(*args, **kwargs)
        self.__logger = logger

    class UpdateController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(VersionController.UpdateController, self).__init__(*args, **kwargs)
            self.__logger = logger

        async def get(self, request):
            username = n_env.user
            api_url = f"{n_env.hub_base}/hub/api"
            r = requests.delete(
                f"{api_url}/users/{username}/server",
                headers={
                    "Authorization": f"token {n_env.token}",
                },
            )
            r.raise_for_status()
            return json({"update": "ok"})
