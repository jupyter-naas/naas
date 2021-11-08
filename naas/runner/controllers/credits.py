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
            res = naascredits.connect().transactions.get(page_size=1000)
            return json(res)

    class BalanceController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(CreditsController.BalanceController, self).__init__(*args, **kwargs)
            self.__logger = logger

        async def get(self, request):
            res = naascredits.connect().get_balance()
            return json(res)
