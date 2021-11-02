from sanic.views import HTTPMethodView
from naas_drivers import naascredits
from sanic.response import json


class CreditsController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(CreditsController, self).__init__(*args, **kwargs)
        self.__logger = logger

    class TransactionController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(CreditsController.TransactionController, self).__init__(
                *args, **kwargs
            )
            self.__logger = logger

        async def get(self, request):
            res = naascredits.connect(
                "bbcbff89afc74001b5975eb9023cbe01"
            ).transactions.get(page_size=1000)
            return json(res)

    class BalanceController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(CreditsController.BalanceController, self).__init__(*args, **kwargs)
            self.__logger = logger

        async def get(self, request):
            res = naascredits.connect("bbcbff89afc74001b5975eb9023cbe01").get_balance()
            return json(res)
