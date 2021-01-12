from naas.types import t_job, t_error, t_send, t_delete
from sanic.views import HTTPMethodView
from sanic import response
import base64
import errno
import uuid
import os

endpoint = "jobs"


class JobsController(HTTPMethodView):
    __jobs = None
    __logger = None
    __min_keys = sorted(list(["path", "type", "params", "value", "status", "file"]))

    def __init__(self, logger, jobs, *args, **kwargs):
        super(JobsController, self).__init__(*args, **kwargs)
        self.__jobs = jobs
        self.__logger = logger

    def __open_file(self, path):
        filename = os.path.basename(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"file doesn't exist {path}")
        data = open(path, "rb").read()
        encoded = base64.b64encode(data)
        return {"filename": filename, "data": encoded.decode("ascii")}

    def __save_file(self, path, data=None):
        if not data:
            raise FileNotFoundError(f"file doesn't have data {path}")
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        f = open(path, "wb")
        decoded = base64.b64decode(data)
        f.write(decoded)
        f.close()

    def __filename_to_filetype(self, path, filetype):
        return path
        # filename = os.path.basename(path)
        # dirname = os.path.dirname(path)
        # filename = f"{filetype}_{filename}"
        # return os.path.join(dirname, filename)

    async def get(self, request):
        uid = str(uuid.uuid4())
        job = None
        data = request.json
        if not data:
            return response.json(await self.__jobs.list(uid))
        else:
            job = await self.__jobs.find_by_path(uid, data["path"], data["type"])
        mode = data.get("mode", None)
        if mode and mode == "list_history":
            job["files"] = self.__jobs.list_files(uid, data["path"], data["type"])
        elif mode and mode == "list_output":
            job["files"] = self.__jobs.list_files(uid, data["path"], data["type"], True)
        elif not mode:
            job["file"] = self.__open_file(
                self.__filename_to_filetype(job["path"], data["type"])
            )
        self.__logger.info(
            {"id": uid, "type": t_job, "status": t_send, "filepath": endpoint}
        )
        return response.json(job)

    async def delete(self, request):
        uid = str(uuid.uuid4())
        data = request.json
        path = data.get("path", None)
        histo = data.get("histo", None)
        path = self.__filename_to_filetype(path, data["type"])
        removed = self.__jobs.clear_file(uid, path, histo)
        if not histo:
            updated = await self.__jobs.update(
                uid,
                path,
                data["type"],
                data["value"],
                {},
                t_delete,
            )
            return response.json(updated)
        return response.json(removed)

    async def post(self, request):
        uid = str(uuid.uuid4())
        data = request.json
        keys = sorted(list(data.keys()))
        if not data or self.__min_keys != keys:
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_job,
                    "status": t_error,
                    "filepath": endpoint,
                    "error": "missing keys",
                    "tb": data,
                }
            )
            return response.json(
                {"id": uid, "status": "error", "error": "missing keys", "data": [data]},
                status=400,
            )
        path = self.__filename_to_filetype(data["path"], data["type"])
        if data.get("file"):
            self.__save_file(path, data["file"]["data"])
        updated = await self.__jobs.update(
            uid,
            path,
            data["type"],
            data["value"],
            data["params"],
            data["status"],
        )
        if updated.get("error"):
            return response.json(updated, status=409)
        self.__logger.info(
            {
                "id": uid,
                "type": t_job,
                "filepath": endpoint,
                "status": updated["status"],
            }
        )
        return response.json(updated)
