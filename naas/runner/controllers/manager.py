from sanic.views import HTTPMethodView
from sanic import response
import os


class ManagerController(HTTPMethodView):
    __path_lib_files = None
    __assets_folder = "assets"
    __manager_html = "manager.html"

    def __init__(self, path_assets, *args, **kwargs):
        super(ManagerController, self).__init__(*args, **kwargs)
        self.__path_lib_files = path_assets

    async def get(self, request):
        return await response.file(
            os.path.join(
                self.__path_lib_files, self.__assets_folder, self.__manager_html
            ),
            headers={"Cache-Control": "no-cache"},
        )
