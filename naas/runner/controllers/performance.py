from sanic.views import HTTPMethodView
from sanic.response import json
from .size import get_folder_size
from naas.runner.env_var import n_env


class PerformanceController(HTTPMethodView):
    def __init__(self, *args, **kwargs):
        super(PerformanceController, self).__init__(*args, **kwargs)

    async def get(self, request, mode=""):
        modes = {
            "cpu": PerformanceController.getCpu,
            "ram": PerformanceController.getRam,
            "storage": PerformanceController.getStorage,
        }
        if modes.get(mode) is not None:
            return json({mode: modes[mode](self)})
        else:
            perf = {}
            for key, value in modes.items():
                perf[key] = value(self)
            return json(perf)

    # TODO make the functions to get the cpu and ram value
    def getCpu(self):
        return "/"

    def getRam(self):
        return "/"

    def getStorage(self):
        return str(get_folder_size(n_env.server_root))
