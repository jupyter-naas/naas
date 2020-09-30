from naas.types import t_notebook, t_health, t_error, t_start
from sanic.views import HTTPMethodView
from sanic.exceptions import ServerError
import uuid


class NbController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, jobs, nb, *args, **kwargs):
        super(NbController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__jobs = jobs
        self.__nb = nb

    async def get(self, request, token):
        uid = str(uuid.uuid4())
        task = await self.__jobs.find_by_value(uid, token, t_notebook)
        if task:
            value = task.get("value", None)
            file_filepath = task.get("path")
            task["params"] = {**(task.get("params", dict())), **(request.args)}
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_notebook,
                    "status": t_start,
                    "filepath": file_filepath,
                    "token": token,
                }
            )
            await self.__jobs.update(
                uid, file_filepath, t_notebook, value, task.get("params"), t_start
            )
            res = await self.__nb.exec(uid, task)
            if res.get("error"):
                self.__logger.error(
                    {
                        "main_id": uid,
                        "id": uid,
                        "type": t_notebook,
                        "status": t_error,
                        "filepath": file_filepath,
                        "duration": res.get("duration"),
                        "error": res.get("error"),
                    }
                )
                await self.__jobs.update(
                    uid,
                    file_filepath,
                    t_notebook,
                    value,
                    task.get("params"),
                    t_error,
                    res.get("duration"),
                )
                raise ServerError(
                    {"id": uid, "error": res.get("error")}, status_code=500
                )
            self.__logger.info(
                {
                    "main_id": uid,
                    "id": uid,
                    "type": t_notebook,
                    "status": t_health,
                    "filepath": file_filepath,
                    "duration": res.get("duration"),
                }
            )
            await self.__jobs.update(
                uid,
                file_filepath,
                t_notebook,
                value,
                task.get("params"),
                t_health,
                res.get("duration"),
            )
            return self.__nb.response(
                uid, file_filepath, res, res.get("duration"), task.get("params")
            )
        self.__logger.error(
            {
                "id": uid,
                "type": t_notebook,
                "status": t_error,
                "token": token,
                "error": "Cannot find your token",
            }
        )
        raise ServerError(
            {"id": uid, "error": "Cannot find your token"}, status_code=404
        )
