from sanic.views import HTTPMethodView
from sanic.response import json


class SchedulerController(HTTPMethodView):
    __scheduler = None

    def __init__(self, scheduler, *args, **kwargs):
        super(SchedulerController, self).__init__(*args, **kwargs)
        self.__scheduler = scheduler

    async def get(self, request, mode):
        if mode == "pause":
            self.__scheduler.pause()
        elif mode == "resume":
            self.__scheduler.resume()
        return json({"status": self.__scheduler.status()})
