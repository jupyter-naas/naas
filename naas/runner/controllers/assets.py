from sanic.views import HTTPMethodView
from sanic import response
from sanic.exceptions import ServerError
from naas.types import t_asset, t_health, t_error, t_start, t_send
import uuid
import os


class AssetsController(HTTPMethodView):
    __logger = None
    __jobs = None
    __path_lib_files = None
    __assets_folder = "assets"

    def __init__(self, logger, jobs, path_assets, *args, **kwargs):
        super(AssetsController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__jobs = jobs
        self.__path_lib_files = path_assets

    async def get(self, request, token):
        if token.startswith("naas_"):
            return await response.file(
                os.path.join(self.__path_lib_files, self.__assets_folder, token)
            )
        else:
            uid = str(uuid.uuid4())
            task = await self.__jobs.find_by_value(uid, token, t_asset)
            if task:
                file_filepath = task.get("path")
                file_name = os.path.basename(file_filepath)
                params = task.get("params", dict())
                inline = params.get("inline", False)
                self.__logger.info(
                    {
                        "id": uid,
                        "type": t_asset,
                        "status": t_start,
                        "filepath": file_filepath,
                        "token": token,
                    }
                )
                try:
                    await self.__jobs.update(
                        uid, file_filepath, t_asset, token, params, t_health, 1
                    )
                    res = await response.file(
                        location=file_filepath,
                        filename=(file_name if not inline else None),
                    )
                    self.__logger.info(
                        {
                            "id": uid,
                            "type": t_asset,
                            "status": t_send,
                            "filepath": file_filepath,
                            "token": token,
                        }
                    )
                    return res
                except Exception as e:
                    self.__logger.error(
                        {
                            "id": uid,
                            "type": t_asset,
                            "status": t_error,
                            "filepath": file_filepath,
                            "token": token,
                            "error": str(e),
                        }
                    )
                    await self.__jobs.update(
                        uid, file_filepath, t_asset, token, params, t_error, 1
                    )
                    raise ServerError({"id": uid, "error": e}, status_code=404)
            self.__logger.error(
                {
                    "id": uid,
                    "type": t_asset,
                    "status": t_error,
                    "error": "Cannot find your token",
                    "token": token,
                }
            )
            raise ServerError(
                {"id": uid, "error": "Cannot find your token", "token": token},
                status_code=404,
            )
