from naas.runner.env_var import n_env
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
    __folder_name = ".naas"
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

    def __get_prod_path(self, path, filetype):
        # filename = os.path.basename(path)
        # dirname = os.path.dirname(path)
        # filename = f"{filetype}_{filename}"
        # path = os.path.join(dirname, filename)
        naas_path = os.path.join(n_env.server_root, self.__folder_name)
        seps = os.sep + os.altsep if os.altsep else os.sep
        strip_path = os.path.splitdrive(path)[1].lstrip(seps)
        new_path = os.path.join(naas_path, strip_path)
        return new_path

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

    async def get(self, request):
        uid = str(uuid.uuid4())
        job = None
        cur_path = request.args.get("path", None)
        cur_type = request.args.get("type", None)
        cur_mode = request.args.get("mode", None)
        cur_light = request.args.get("light", False)
        if not cur_path or not cur_type:
            return response.json(await self.__jobs.list(uid))
        path = self.__get_prod_path(cur_path, cur_type)
        job = await self.__jobs.find_by_path(uid, path, cur_type)
        if not job:
            return response.json({"error": "job not found"}, status=500)
        if cur_mode and cur_mode == "list_history":
            job["files"] = self.__jobs.list_files(uid, path, cur_type)
        elif cur_mode and cur_mode == "list_output":
            job["files"] = self.__jobs.list_files(uid, path, cur_type, True)
        elif not cur_mode and not cur_light:
            job["file"] = self.__open_file(path)
        self.__logger.info(
            {"id": uid, "type": t_job, "status": t_send, "filepath": endpoint}
        )
        return response.json(job)

    async def delete(self, request):
        uid = str(uuid.uuid4())
        data = request.json
        histo = data.get("histo", None)
        path = self.__get_prod_path(data.get("path", None), data["type"])
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
        path = self.__get_prod_path(data["path"], data["type"])
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
