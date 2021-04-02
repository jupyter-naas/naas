from .controllers.downloader import DownloaderController
from sentry_sdk.integrations.sanic import SanicIntegration
from .controllers.scheduler import SchedulerController
from .controllers.manager import ManagerController
from .controllers.assets import AssetsController
from .controllers.secret import SecretController
from .controllers.notebooks import NbController
from .controllers.timezone import TimezoneController
from .controllers.jobs import JobsController
from .controllers.logs import LogsController
from sanic_openapi import swagger_blueprint
from .controllers.env import EnvController
from .controllers.size import SizeController
from .notifications import Notifications
from naas.onboarding import init_onborading
from .proxy import escape_kubernet
from .scheduler import Scheduler
from .notebooks import Notebooks
from .env_var import n_env
from .logger import Logger
from .jobs import Jobs
from .secret import Secret
from sanic import Sanic
import nest_asyncio
import sentry_sdk
import asyncio
import getpass
import uuid
import os
import sys
import errno
from naas.ntypes import (
    t_main,
    t_notebook,
    t_scheduler,
    t_asset,
    t_job,
    t_secret,
    t_tz,
    t_downloader,
)

# TODO remove this fix when papermill and nest_asyncio support uvloop
asyncio.set_event_loop_policy(None)
nest_asyncio.apply()

__version__ = "1.9.9"


class Runner:
    # Declare path variable
    __path_lib_files = os.path.dirname(os.path.abspath(__file__))
    __app = None
    __nb = None
    __notif = None
    __jobs = None
    __scheduler = None
    __logger = None

    def __main(self, debug=True):
        self.init_app()
        uid = str(uuid.uuid4())
        self.__logger.info(
            {"id": uid, "type": t_main, "filepath": "runner", "status": "start API"}
        )
        self.__app.run(
            host="0.0.0.0", port=n_env.api_port, debug=debug, access_log=debug
        )

    async def initialize_before_start(self, app, loop):
        init_onborading()
        if self.__jobs is None:
            self.__jobs = Jobs(self.__logger)
            self.__secret = Secret(self.__logger)
            self.__nb = Notebooks(self.__logger, self.__notif)
            self.__app.add_route(
                NbController.as_view(self.__logger, self.__jobs, self.__nb),
                f"/{t_notebook}/<token>",
            )
            if n_env.scheduler:
                self.__scheduler = Scheduler(
                    self.__logger, self.__jobs, self.__nb, loop
                )
            self.__app.add_route(
                SchedulerController.as_view(self.__scheduler, self.__logger),
                f"/{t_scheduler}/<mode>",
            )
            self.__app.add_route(
                DownloaderController.as_view(self.__logger),
                f"/{t_downloader}",
            )
            self.__app.add_route(
                AssetsController.as_view(
                    self.__logger, self.__jobs, self.__path_lib_files
                ),
                f"/{t_asset}/<token>",
            )
            self.__app.add_route(
                EnvController.as_view(),
                "/env",
            )
            self.__app.add_route(
                SizeController.as_view(),
                "/size",
            )
            self.__app.add_route(LogsController.as_view(self.__logger), "/log")
            self.__app.add_route(
                ManagerController.as_view(self.__path_lib_files),
                "/",
            )
            self.__app.add_route(
                JobsController.as_view(self.__logger, self.__jobs), f"/{t_job}"
            )
            self.__app.add_route(TimezoneController.as_view(self.__logger), f"/{t_tz}")
            self.__app.add_route(
                SecretController.as_view(self.__logger, self.__secret), f"/{t_secret}"
            )
            if n_env.scheduler:
                await self.__scheduler.start()

    async def initialize_before_stop(self, app, loop):
        if n_env.scheduler and self.__scheduler is not None:
            self.__scheduler.stop()
            self.__scheduler = None
        if self.__nb is not None:
            self.__nb = None
        if self.__jobs is not None:
            self.__jobs = None
        if self.__logger is not None:
            self.__logger = None

    def init_app(self):
        if not os.path.exists(n_env.path_naas_folder):
            try:
                print("Init Naas folder Jobs")
                os.makedirs(n_env.path_naas_folder)
            except OSError as exc:  # Guard against race condition
                print("__path_naas_files", n_env.path_naas_folder)
                if exc.errno != errno.EEXIST:
                    raise
            except Exception as e:
                print("Exception", e)
        self.__app = Sanic(__name__)
        self.__logger = Logger()
        self.__notif = Notifications(self.__logger)
        self.__app.register_listener(
            self.initialize_before_start, "before_server_start"
        )
        self.__app.register_listener(self.initialize_before_stop, "before_server_stop")
        self.__app.blueprint(swagger_blueprint)
        uid = str(uuid.uuid4())
        self.__logger.info(
            {"id": uid, "type": t_main, "filepath": "runner", "status": "init API"}
        )
        return self.__app

    async def kill(self):
        await self.__app.stop()

    def start(self, port=None, debug=False):
        user = getpass.getuser()
        if user != n_env.shell_user:
            raise ValueError(f"{user} not autorized, use {n_env.shell_user} instead")
        if port:
            n_env.api_port = port
        print("Start Runner", __version__)
        try:
            if n_env.sentry_dsn:
                sentry_sdk.init(
                    dsn=n_env.sentry_dsn,
                    traces_sample_rate=1.0,
                    environment=escape_kubernet(n_env.user),
                    integrations=[SanicIntegration()],
                )
                sentry_sdk.set_user({"email": n_env.user})
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("Naas", {"version": __version__})
            self.__main(debug)
        except KeyboardInterrupt:
            print("Shutdown server")
            sys.exit()
