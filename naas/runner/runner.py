from naas.types import t_main, t_notebook, t_scheduler, t_asset, t_job, t_secret
from sentry_sdk.integrations.sanic import SanicIntegration
from .controllers.scheduler import SchedulerController
from .controllers.assets import AssetsController
from .controllers.secret import SecretController
from .controllers.notebooks import NbController
from .controllers.jobs import JobsController
from .controllers.logs import LogsController
from sanic_openapi import swagger_blueprint
from .controllers.env import EnvController
from .notifications import Notifications
from .proxy import escape_kubernet
from .scheduler import Scheduler
from .notebooks import Notebooks
from .env_var import n_env
from .logger import Logger
from .jobs import Jobs
from .secret import Secret
from sanic import Sanic
import sentry_sdk
import asyncio
import getpass
import uuid
import os
import sys
import errno
import nest_asyncio

# TODO remove this fix when papermill support uvloop of Sanic support option to don't use uvloop
asyncio.set_event_loop_policy(None)
nest_asyncio.apply()

__version__ = "0.26.2"


class Runner:
    __naas_folder = ".naas"
    # Declare path variable
    __path_lib_files = os.path.dirname(os.path.abspath(__file__))
    __html_files = "html"
    __manager_index = "manager.html"
    __app = None
    __nb = None
    __notif = None
    __jobs = None
    __scheduler = None
    __logger = None

    def __init__(self):
        self.__path_naas_files = os.path.join(n_env.server_root, self.__naas_folder)
        self.__path_html_files = os.path.join(self.__path_lib_files, self.__html_files)
        self.__path_manager_index = os.path.join(
            self.__path_html_files, self.__manager_index
        )

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
                AssetsController.as_view(
                    self.__logger, self.__jobs, self.__path_lib_files
                ),
                f"/{t_asset}/<token>",
            )
            self.__app.add_route(
                JobsController.as_view(self.__logger, self.__jobs), f"/{t_job}"
            )
            self.__app.add_route(
                SecretController.as_view(self.__logger, self.__secret), f"/{t_secret}"
            )
            if n_env.scheduler:
                await self.__scheduler.start()

    def initialize_before_stop(self, app, loop):
        if self.__nb is not None:
            self.__nb = None
        if n_env.scheduler and self.__scheduler is not None:
            self.__scheduler.stop()
            self.__scheduler = None
        if self.__jobs is not None:
            self.__jobs = None

    def init_app(self):
        if not os.path.exists(self.__path_naas_files):
            try:
                print("Init Naas folder Jobs")
                os.makedirs(self.__path_naas_files)
            except OSError as exc:  # Guard against race condition
                print("__path_naas_files", self.__path_naas_files)
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
        self.__app.add_route(
            EnvController.as_view(
                self.__logger,
                n_env.user,
                n_env.hub_api,
                n_env.proxy_api,
                n_env.notif_api,
                n_env.tz,
                n_env.server_root,
            ),
            "/env",
        )
        self.__app.add_route(LogsController.as_view(self.__logger), "/log")
        self.__app.static("/", self.__path_manager_index, name="manager.html")
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
