from naas.ntypes import t_notebook, t_health, t_error, t_start, t_delete
from sanic.views import HTTPMethodView
from sanic.exceptions import ServerError
import urllib
import uuid


def parse_data(request):
    req_data = {}
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("multipart/form-data"):
        req_data = request.files
    elif ctype.startswith("application/json"):
        req_data = request.json
    elif ctype.startswith("application/x-www-form-urlencoded"):
        req_data = dict(urllib.parse.parse_qsl(request.body.decode("utf-8")))
    else:
        req_data = str(request.body.decode("utf-8"))
    args = dict(
        urllib.parse.parse_qsl(request.query_string)
    )  # fix to don't have array for each args
    data = {"params": args, "body": req_data, "headers": dict(request.headers)}
    return data


class NbController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, jobs, nb, *args, **kwargs):
        super(NbController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__jobs = jobs
        self.__nb = nb

    async def _get(self, data, token):
        uid = str(uuid.uuid4())
        job = await self.__jobs.find_by_value(uid, token, t_notebook)
        if job and job.get("status") != t_delete:
            value = job.get("value", None)
            file_filepath = job.get("path")
            cur_job = job.copy()
            cur_job["params"] = {**(job.get("params", dict())), **(data)}
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
                uid, file_filepath, t_notebook, value, job.get("params"), t_start
            )
            res = await self.__nb.exec(uid, cur_job)
            if res.get("error"):
                self.__logger.error(
                    {
                        "main_id": uid,
                        "id": uid,
                        "type": t_notebook,
                        "status": t_error,
                        "filepath": file_filepath,
                        "duration": res.get("duration"),
                        "error": str(res.get("error")),
                    }
                )
                await self.__jobs.update(
                    uid,
                    file_filepath,
                    t_notebook,
                    value,
                    job.get("params"),
                    t_error,
                    res.get("duration"),
                )
                raise ServerError(
                    {
                        "id": uid,
                        "error": res.get("error"),
                        "data": data,
                        "token": token,
                    },
                    status_code=500,
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
                job.get("params"),
                t_health,
                res.get("duration"),
            )
            return self.__nb.response(
                uid, file_filepath, res, res.get("duration"), job.get("params")
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
            {
                "id": uid,
                "error": "Cannot find your token",
                "data": data,
                "token": token,
            },
            status_code=404,
        )

    async def get(self, request, token):
        return await self._get(parse_data(request), token)

    async def post(self, request, token):
        return await self._get(parse_data(request), token)
