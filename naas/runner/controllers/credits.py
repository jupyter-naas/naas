from sanic.views import HTTPMethodView
from naas_drivers import naascredits
from sanic.response import json
import os

TOKEN = os.environ.get("PROD_JUPYTERHUB_API_TOKEN", None)


class CreditsController(HTTPMethodView):
    __logger = None

    def __init__(self, logger, *args, **kwargs):
        super(CreditsController, self).__init__(*args, **kwargs)
        self.__logger = logger

    class PlanController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(CreditsController.PlanController, self).__init__(*args, **kwargs)
            self.__logger = logger

        async def get(self, request):
            res = naascredits.connect(TOKEN).get_plan()
            return json(res)

    class TransactionController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(CreditsController.TransactionController, self).__init__(
                *args, **kwargs
            )
            self.__logger = logger

        async def get(self, request):
            res = naascredits.connect(TOKEN).transactions.get(page_size=1000)
            return json(res)

    class BalanceController(HTTPMethodView):
        __logger = None

        def __init__(self, logger, *args, **kwargs):
            super(CreditsController.BalanceController, self).__init__(*args, **kwargs)
            self.__logger = logger

        async def get(self, request):
            res = naascredits.connect(TOKEN).get_balance()
            return json(res)
