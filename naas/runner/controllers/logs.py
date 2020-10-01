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
            limit = int(request.args.get("limit", 0))
            skip = int(request.args.get("skip", 0))
            search = str(request.args.get("search", ""))
            filters = list(request.args.get("filters", []))
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
