from sanic.response import redirect, text
from sanic.views import HTTPMethodView
from naas.runner.env_var import n_env
from naas.types import t_downloader
import urllib.parse
import traceback
import requests
import uuid


class DownloaderController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(DownloaderController, self).__init__(*args, **kwargs)
        self.__logger = logger

    async def get(self, request):
        uid = str(uuid.uuid4())
        target = str(request.args.get("url", ""))
        try:
            raw_target = target
            if "github.com" in raw_target:
                raw_target = raw_target.replace(
                    "https://github.com/", "https://raw.githubusercontent.com/"
                )
                raw_target = raw_target.replace("/blob/", "/")
            r = requests.get(raw_target)

            file_name = raw_target.split("/")[-1]
            file_name = urllib.parse.unquote(file_name)

            with open(file_name, "wb") as f:
                f.write(r.content)
            self.__logger.info(
                {"id": uid, "type": t_downloader, "status": "send", "filepath": target}
            )
            if "http" not in n_env.user_url:
                redirect_to = (
                    f"{request.scheme}://{n_env.user_url}/lab/tree/{file_name}"
                )
            else:
                redirect_to = f"{n_env.user_url}/lab/tree/{file_name}"
            return redirect(redirect_to)
        except Exception as e:
            tb = traceback.format_exc()
            self.__logger.error(
                {"id": uid, "type": t_downloader, "status": "send", "filepath": target}
            )
            return text(e, tb)
