from sanic.views import HTTPMethodView
from sanic import response
from naas.ntypes import t_log, t_send
import uuid
import json

endpoint = "logs"


class LogsController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(LogsController, self).__init__(*args, **kwargs)
        self.__logger = logger

    async def get(self, request):
        as_file = request.args.get("as_file", False)
        if as_file:
            return await response.file(
                self.__logger.get_file_path(), filename="logs.csv"
            )
        else:
            uid = str(uuid.uuid4())
            limit = int(request.args.get("limit", 0))
            skip = int(request.args.get("skip", 0))
            search = str(request.args.get("search", ""))
            sort = list(json.loads(request.args.get("sort", "[]")))
            filters = list(json.loads(request.args.get("filters", "[]")))
            technical_rows = bool(
                json.loads(request.args.get("technical_rows", "true"))
            )
            logs = self.__logger.list(
                uid, skip, limit, search, filters, sort, technical_rows
            )
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_log,
                    "status": t_send,
                    "filepath": endpoint,
                    "skip": skip,
                    "limit": limit,
                    "search": search,
                    "filters": filters,
                    "sort": sort,
                }
            )
            return response.json(logs)
