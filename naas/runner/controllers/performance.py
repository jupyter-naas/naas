from sanic.views import HTTPMethodView
from sanic.response import json
from .size import get_folder_size
from naas.runner.env_var import n_env


class PerformanceController(HTTPMethodView):
    def __init__(self, *args, **kwargs):
        super(PerformanceController, self).__init__(*args, **kwargs)

    async def get(self, request):
        performance = {
            "cpu": "/",
            "ram": "/",
            "storage": str(get_folder_size(n_env.server_root))
        }
        return json(performance)
