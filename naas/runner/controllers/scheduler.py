from sanic.views import HTTPMethodView
from sanic.response import json
from naas.types import t_static, t_notebook, t_health, t_error
import uuid

class SchedulerController(HTTPMethodView):
    __logger = None
    __scheduler = None
    
    def __init__(self, logger, scheduler, *args, **kwargs):
        super(SchedulerController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__scheduler = scheduler
    
    async def get(self, request, mode):
        if (mode == 'pause'):
            self.__scheduler.pause()
        elif (mode == 'resume'):
            self.__scheduler.resume()
        return json({"status": self.__scheduler.status()})