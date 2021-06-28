from notebook.services.contents.filemanager import FileContentsManager as FCM
from naas.onboarding import download_file
from sanic.response import redirect, json
from sanic.views import HTTPMethodView
from naas.runner.env_var import n_env
from naas.ntypes import t_downloader, t_send, t_error
import traceback
import uuid


class DownloaderController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(DownloaderController, self).__init__(*args, **kwargs)
        self.__logger = logger

    async def get(self, request):
        uid = str(uuid.uuid4())
        url = request.args.get("url", None)
        mode_api = request.args.get("api", None)
        file_name = request.args.get("name", None)
        if url is None and file_name is None:
            return json({"status": t_error})
        if url is None:
            try:
                file_name = f"{file_name}.ipynb"
                FCM().new(path=file_name)
            except Exception as e:
                tb = traceback.format_exc()
                self.__logger.error(
                    {"id": uid, "type": t_downloader, "status": t_send, "filepath": url}
                )
                return json({"status": t_error, "error": str(e), "tb": str(tb)})
        else:
            try:
                file_name = download_file(url, file_name)
                self.__logger.info(
                    {"id": uid, "type": t_downloader, "status": t_send, "filepath": url}
                )
            except Exception as e:
                tb = traceback.format_exc()
                self.__logger.error(
                    {"id": uid, "type": t_downloader, "status": t_send, "filepath": url}
                )
                return json({"status": t_error, "error": str(e), "tb": str(tb)})
        if mode_api is None:
            redirect_to = f"{n_env.user_url}/lab/tree/{file_name}"
            return redirect(redirect_to)
        else:
            return json({"status": t_send})
