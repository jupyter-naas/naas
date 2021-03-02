from notebook.services.contents.filemanager import FileContentsManager as FCM
from naas.onboarding import download_file, wp_set_for_open_filebrowser
from sanic.response import redirect, json
from sanic.views import HTTPMethodView
from naas.runner.env_var import n_env
from naas.types import t_downloader
import traceback
import uuid


class DownloaderController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(DownloaderController, self).__init__(*args, **kwargs)
        self.__logger = logger

    async def get(self, request):
        uid = str(uuid.uuid4())
        url = str(request.args.get("url", ""))
        mode_api = request.args.get("api", None)
        create = str(request.args.get("create", ""))
        redirect_to = None
        if create and create != "":
            try:
                notebook_fname = f"{create}.ipynb"
                FCM().new(path=notebook_fname)
                wp_set_for_open_filebrowser(notebook_fname)
                redirect_to = f"{n_env.user_url}/lab"
            except Exception as e:
                tb = traceback.format_exc()
                self.__logger.error(
                    {"id": uid, "type": t_downloader, "status": "send", "filepath": url}
                )
                return json({"status": e, "tb": str(tb)})
        else:
            try:
                file_name = download_file(url)
                wp_set_for_open_filebrowser(file_name)
                self.__logger.info(
                    {"id": uid, "type": t_downloader, "status": "send", "filepath": url}
                )
                redirect_to = f"{n_env.user_url}/lab"
            except Exception as e:
                tb = traceback.format_exc()
                self.__logger.error(
                    {"id": uid, "type": t_downloader, "status": "send", "filepath": url}
                )
                return json({"status": e, "tb": str(tb)})
        if mode_api is None:
            return redirect(redirect_to)
        else:
            return json({"status": "ok"})
