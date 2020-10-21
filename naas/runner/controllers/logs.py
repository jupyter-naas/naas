from sanic.views import HTTPMethodView
from sanic.response import json, file
from naas.types import t_asset
import uuid


class LogsController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(LogsController, self).__init__(*args, **kwargs)
        self.__logger = logger

    async def get(self, request):
        as_file = request.args.get("as_file", False)
        if as_file:
            return await file(self.__logger.get_file_path(), filename="logs.csv")
        else:
            uid = str(uuid.uuid4())
            data = request.json if request.json else {}
            limit = int(request.args.get("limit") or data.get("limit") or 0)
            skip = int(request.args.get("skip") or data.get("skip") or 0)
            search = str(request.args.get("search") or data.get("search") or "")
            filters = list(request.args.get("filters") or data.get("filters") or [])
            logs = self.__logger.list(uid, skip, limit, search, filters)
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_asset,
                    "status": "send",
                    "filepath": "logs",
                    "skip": skip,
                    "limit": limit,
                    "search": search,
                    "filters": filters,
                }
            )
            return json(logs)
