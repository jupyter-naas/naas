from sanic.views import HTTPMethodView
from sanic import response
from sanic.exceptions import ServerError
from naas.ntypes import (
    t_asset,
    t_health,
    t_error,
    t_start,
    t_send,
    t_delete,
    t_out_of_credits,
)
import uuid
import os
import pydash as _
from naas_drivers import naascredits


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
            job = await self.__jobs.find_by_value(uid, token, t_asset)
            if job and job.get("status") != t_delete:
                file_filepath = job.get("path")
                file_name = os.path.basename(file_filepath)
                params = job.get("params", dict())
                inline = params.get("inline", False)
                if not os.environ.get(
                    "JUPYTERHUB_API_TOKEN"
                ) is None and "app.naas.ai" in os.environ.get("JUPYTERHUB_URL", ""):
                    if _.get(naascredits.connect().get_balance(), "balance") <= 0:
                        self.__logger.info(
                            {
                                "id": uid,
                                "type": t_asset,
                                "status": t_out_of_credits,
                                "filepath": file_filepath,
                                "token": token,
                            }
                        )
                        raise ServerError(
                            {"error": "Out of credits"},
                            status_code=401,
                        )

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
