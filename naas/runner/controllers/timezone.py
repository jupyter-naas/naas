from naas.ntypes import t_tz, t_send, t_error, t_update
from sanic.views import HTTPMethodView
from naas.runner.env_var import n_env
from sanic import response
import uuid
import pytz


class TimezoneController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(TimezoneController, self).__init__(*args, **kwargs)
        self.__logger = logger

    def post(self, request):
        data = request.json
        tz = data.get("tz")
        uid = str(uuid.uuid4())
        if tz and tz in pytz.all_timezones:
            n_env.tz = tz
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_tz,
                    "status": t_update,
                    "filepath": t_tz,
                }
            )
            return response.json({"tz": str(n_env.tz)})
        else:
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_tz,
                    "status": t_error,
                    "filepath": t_tz,
                }
            )
            return response.json({"error": "this timezone don't exist"})

    async def get(self, request):
        uid = str(uuid.uuid4())
        self.__logger.info(
            {
                "id": uid,
                "type": t_tz,
                "status": t_send,
                "filepath": t_tz,
            }
        )
        return response.json({"tz": str(n_env.tz)})
