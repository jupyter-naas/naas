from sentry_sdk.integrations.sanic import SanicIntegration
from naas.runner.controllers.scheduler import SchedulerController
from naas.runner.controllers.static import StaticController
from naas.runner.controllers.notebooks import NbController
from naas.runner.controllers.jobs import JobsController
from naas.runner.controllers.logs import LogsController
from naas.runner.controllers.env import EnvController
from naas.runner.notifications import Notifications
from naas.runner.scheduler import Scheduler
from naas.runner.notebooks import Notebooks
from sanic_openapi import swagger_blueprint
from naas.runner.logger import Logger
from .proxy import escape_kubernet
from naas.runner.jobs import Jobs
from daemonize import Daemonize
from naas.types import t_main
from datetime import datetime
from sanic import Sanic
import sentry_sdk
import getpass
import uuid
import os

class Runner():
    # Declare semaphore variable
    __name = 'naas_runner'
    __naas_folder = '.naas'
    __tasks_sem = None
    # Declare path variable
    __path_lib_files = os.path.dirname(os.path.abspath(__file__))
    __path_user_files = None
    __port = 5000
    __single_user_api_path = None
    __html_files = 'html'
    __assets_files = 'assets'
    __manager_index = 'manager.html'
    __log_filename = 'logs.csv'
    __tasks_files = 'jobs.json'
    __info_file = 'info.json'
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
        self.__path_user_files = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
        self.__port = int(os.environ.get('NAAS_RUNNER_PORT', 5000))
        self.__user = os.environ.get('JUPYTERHUB_USER', 'joyvan@naas.com')
        self.__shell_user = os.environ.get('USER', None)
        self.__public_url = os.environ.get('JUPYTERHUB_URL', f'http://localhost:{self.__port}')
        self.__proxy_url = os.environ.get('PUBLIC_PROXY_API', 'http://localhost:5002')
        self.__tz = os.environ.get('TZ', 'Europe/Paris')
        self.__path_naas_files = os.path.join(self.__path_user_files, self.__naas_folder)
        self.__path_html_files = os.path.join(self.__path_lib_files, self.__html_files)
        self.__path_manager_index = os.path.join(self.__path_html_files, self.__manager_index)
        self.__path_pidfile = os.path.join(self.__path_naas_files, f'{self.__name}.pid')

    def __main(self, debug=False):
        uid = str(uuid.uuid4())
        self.__logger.info(
            {'id': uid, 'type': t_main, "status": 'start API'})
        self.__app.run(host="0.0.0.0", port=self.__port, debug=debug, access_log=debug)

    def __version(self):
        version = None
        try:
            with open(os.path.join(self.__path_lib_files, self.__info_file), 'r') as json_file:
                version = json.load(json_file)
        except:
            version = {'error': 'cannot get info.json'}
        return version

    async def initialize_before_start(self, app, loop):
        if self.__nb is None:
            self.__nb = Notebooks(self.__logger, loop, self.__notif)
            self.__app.add_route(NbController.as_view(self.__logger, self.__jobs, self.__nb), '/notebooks/<token>')
            self.__scheduler = Scheduler(self.__logger, self.__jobs, loop)
            self.__app.add_route(SchedulerController.as_view(self.__logger, self.__scheduler), '/scheduler/<mode>')
            self.__scheduler.start()

    def kill(self):
        if os.path.exists(self.__path_pidfile):
            try:
                with open(self.__path_pidfile, 'r') as f:
                    pid = f.read()
                    print('kill')
                    os.system(f'kill {pid}')
                    print(f'Deamon killed pid {pid}')
                    f.close()
            except Exception:
                print('No Deamon running')

    def init_app(self):
        self.__logger = Logger()
        self.__notif = Notifications(self.__logger)
        self.__jobs = Jobs(self.__logger)
        self.__app = Sanic(__name__)
        self.__app.register_listener(self.initialize_before_start, 'before_server_start')
        self.__app.add_route(EnvController.as_view(self.__logger, self.__version, self.__user, self.__public_url, self.__proxy_url, self.__tz), '/env')
        self.__app.add_route(LogsController.as_view(self.__logger), '/logs')
        self.__app.add_route(JobsController.as_view(self.__logger, self.__jobs), '/jobs')
        self.__app.add_route(StaticController.as_view(self.__logger,  self.__jobs, self.__path_lib_files), '/static/<token>')
        self.__app.static('/', self.__path_manager_index, name='manager.html')
        self.__app.blueprint(swagger_blueprint)
        uid = str(uuid.uuid4())
        self.__logger.info(
            {'id': uid, 'type': t_main, "status": 'init API'})
        return self.__app
                
    def start(self, deamon=True, port=None, debug=True):
        user = getpass.getuser()
        if (user != self.__shell_user):
            raise Exception(f"{user} not autorized, use {self.__shell_user} instead")
        self.kill()
        if port:
            self.__port = port
        self.init_app()
        if deamon:
            if (os.environ.get('NAAS_SENTRY_DSN')):
                self.__sentry = sentry_sdk.init(
                    dsn=os.environ.get('NAAS_SENTRY_DSN'),
                    traces_sample_rate=1.0,
                    environment=escape_kubernet(self.__user),
                    integrations=[SanicIntegration()]
                )
            self.__daemon = Daemonize(app=self.__name, pid=self.__path_pidfile, action=self.__main)
            print('Start Runner Deamon Mode')
            self.__daemon.start()
        else:
            print('Start Runner front Mode')
            try:
                self.__main(debug)
            except KeyboardInterrupt:
                print('Shutdown server')
                sys.exit()
    