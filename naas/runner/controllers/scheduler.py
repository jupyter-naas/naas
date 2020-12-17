from sanic.views import HTTPMethodView
from naas.types import t_scheduler
from sanic.response import json
import uuid

endpoint = "schedulers"


class SchedulerController(HTTPMethodView):
    __scheduler = None

    def __init__(self, scheduler, logger, *args, **kwargs):
        super(SchedulerController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__scheduler = scheduler

    async def _get(self, request, mode):
        uid = str(uuid.uuid4())
        if mode == "pause":
            self.__scheduler.pause()
        elif mode == "resume":
            self.__scheduler.resume()
        self.__logger.info(
            {"id": uid, "type": t_scheduler, "status": "send", "filepath": endpoint}
        )
        return json({"status": self.__scheduler.status()})

    async def get(self, request, mode):
        return await self._get(request, mode)

    async def post(self, request, mode):
        return await self._get(request, mode)
