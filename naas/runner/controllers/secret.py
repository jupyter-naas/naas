from sanic.views import HTTPMethodView
from sanic import response
from naas.types import t_secret, t_error, t_send
import uuid


class SecretController(HTTPMethodView):
    __secrets = None
    __logger = None
    __min_keys = sorted(list(["name", "secret", "status"]))

    def __init__(self, logger, secrets, *args, **kwargs):
        super(SecretController, self).__init__(*args, **kwargs)
        self.__secrets = secrets
        self.__logger = logger

    async def get(self, request):
        uid = str(uuid.uuid4())
        status = await self.__secrets.list(uid)
        self.__logger.info(
            {"id": uid, "type": t_secret, "status": t_send, "filepath": t_secret}
        )
        return response.json(status)

    async def post(self, request):
        uid = str(uuid.uuid4())
        data = request.json
        keys = sorted(list(data.keys()))
        if not data or self.__min_keys != keys:
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_secret,
                    "status": t_error,
                    "filepath": t_secret,
                    "error": "missing keys",
                    "tb": data,
                }
            )
            return response.json(
                {"id": uid, "status": "error", "error": "missing keys", "data": [data]},
                status=400,
            )
        updated = await self.__secrets.update(
            uid,
            data["name"],
            data["secret"],
            data["status"],
        )
        if updated.get("error"):
            return response.json(updated, status=409)
        self.__logger.info(
            {
                "id": uid,
                "type": t_secret,
                "filepath": t_secret,
                "status": updated["status"],
            }
        )
        return response.json(updated)
