from naas.types import t_main, t_notebook, t_scheduler, t_asset, t_job
from sentry_sdk.integrations.sanic import SanicIntegration
from .controllers.scheduler import SchedulerController
from .controllers.assets import AssetsController
from .controllers.notebooks import NbController
from .controllers.jobs import JobsController
from .controllers.logs import LogsController
from .controllers.env import EnvController
from .notifications import Notifications
from .scheduler import Scheduler
from .notebooks import Notebooks
from sanic_openapi import swagger_blueprint
from .logger import Logger
from .proxy import escape_kubernet
from .jobs import Jobs

# from naas.__version__ import __version__
from sanic import Sanic
import sentry_sdk
import asyncio
import getpass
import uuid
import os
import json
import sys
import errno
import nest_asyncio

# TODO remove this fix when papermill support uvloop of Sanic support option to don't use uvloop
asyncio.set_event_loop_policy(None)
nest_asyncio.apply()

__version__ = "0.5.7"


class Runner:
    # Declare semaphore variable
    __name = "naas_runner"
    __naas_folder = ".naas"
    __tasks_sem = None
    # Declare path variable
    __path_lib_files = os.path.dirname(os.path.abspath(__file__))
    __path_user_files = None
    __port = 5000
    __single_user_api_path = None
    __html_files = "html"
    __assets_files = "assets"
    __manager_index = "manager.html"
    __log_filename = "logs.csv"
    __tasks_files = "jobs.json"
    __info_file = "info.json"
    __app = None
    __nb = None
    __http_server = None
    __notif = None
    __jobs = None
    __scheduler = None
    __daemon = None
    __sentry = None
    __logger = None
    __testing = False
    tz = None
    user = None
    __shell_user = None
    public_url = None
    proxy_url = None

    def __init__(self):
        self.__path_user_files = os.environ.get(
            "JUPYTER_SERVER_ROOT", f'/home/{os.environ.get("NB_USER", "ftp")}'
        )
        self.__port = int(os.environ.get("NAAS_RUNNER_PORT", 5000))
        self.__user = os.environ.get("JUPYTERHUB_USER", "joyvan@naas.com")
        self.__shell_user = os.environ.get("NB_USER", None)
        self.__public_url = os.environ.get("JUPYTERHUB_URL", "")
        self.__proxy_url = os.environ.get("PUBLIC_PROXY_API", "http://localhost:3002")
        self.__notifications_url = os.environ.get(
            "NOTIFICATIONS_API", "http://localhost:3003"
        )
        self.__tz = os.environ.get("TZ", "Europe/Paris")
        self.__path_naas_files = os.path.join(
            self.__path_user_files, self.__naas_folder
        )
        self.__path_html_files = os.path.join(self.__path_lib_files, self.__html_files)
        self.__path_manager_index = os.path.join(
            self.__path_html_files, self.__manager_index
        )
        self.__path_pidfile = os.path.join(self.__path_naas_files, f"{self.__name}.pid")

    def __main(self, debug=True):
        self.init_app()
        uid = str(uuid.uuid4())
        self.__logger.info({"id": uid, "type": t_main, "status": "start API"})
        self.__app.run(host="0.0.0.0", port=self.__port, debug=debug, access_log=debug)

    def __version(self):
        version = None
        try:
            with open(
                os.path.join(self.__path_lib_files, self.__info_file), "r"
            ) as json_file:
                version = json.load(json_file)
        except IOError:
            version = {"error": "cannot get info.json"}
        return version

    async def initialize_before_start(self, app, loop):
        if self.__jobs is None:
            self.__jobs = Jobs(self.__logger)
            self.__nb = Notebooks(self.__logger, self.__notif)
            self.__app.add_route(
                NbController.as_view(self.__logger, self.__jobs, self.__nb),
                f"/{t_notebook}/<token>",
            )
            self.__scheduler = Scheduler(self.__logger, self.__jobs, self.__nb, loop)
            self.__app.add_route(
                SchedulerController.as_view(self.__logger, self.__scheduler),
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
            await self.__scheduler.start()

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
        self.__app.add_route(
            EnvController.as_view(
                self.__logger,
                self.__user,
                self.__public_url,
                self.__proxy_url,
                self.__notifications_url,
                self.__tz,
            ),
            "/env",
        )
        self.__app.add_route(LogsController.as_view(self.__logger), "/log")
        self.__app.static("/", self.__path_manager_index, name="manager.html")
        self.__app.blueprint(swagger_blueprint)
        uid = str(uuid.uuid4())
        self.__logger.info({"id": uid, "type": t_main, "status": "init API"})
        return self.__app

    def start(self, deamon=True, port=None, debug=False):
        user = getpass.getuser()
        if user != self.__shell_user:
            raise Exception(f"{user} not autorized, use {self.__shell_user} instead")
        if port:
            self.__port = port
        print("Start Runner", __version__)
        try:
            if os.environ.get("NAAS_SENTRY_DSN"):
                self.__sentry = sentry_sdk.init(
                    dsn=os.environ.get("NAAS_SENTRY_DSN"),
                    traces_sample_rate=1.0,
                    environment=escape_kubernet(self.__user),
                    integrations=[SanicIntegration()],
                )
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context("Naas", {"version": __version__})
            self.__main(debug)
        except KeyboardInterrupt:
            print("Shutdown server")
            sys.exit()
