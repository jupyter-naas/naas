from tzlocal import get_localzone
from pathlib import Path
import os


class n_env:
    _api = None
    _version = None
    _remote_mode = False
    _api_port = None
    _notif_api = None
    _callback_api = None
    _report_callback = False
    _proxy_api = None
    _hub_base = None

    _naas_folder = None

    _current = {}

    _custom_path = None
    _server_root = None
    _shell_user = None

    _token = None
    _user = None
    _tz = None
    _sentry_dsn = None
    _scheduler = True
    _scheduler_interval = None
    _scheduler_job_max = None
    _scheduler_job_name = None
    _scheduler_timeout = None

    @property
    def api_port(self):
        return self._api_port or os.environ.get("NAAS_API_PORT", "5000")

    @api_port.setter
    def api_port(self, api_port: int):
        self._api_port = api_port

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, current):
        self._current = current

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version: str):
        self._version = version

    @property
    def remote_mode(self):
        return self._remote_mode

    @remote_mode.setter
    def remote_mode(self, remote_mode):
        self._remote_mode = remote_mode

    @property
    def api(self):
        return self._api or os.environ.get(
            "NAAS_API",
            f"http://localhost:{self.api_port}"
            if not self.remote_mode
            else self.remote_api,
        )

    @api.setter
    def api(self, api):
        self._api = api

    @property
    def notif_api(self):
        return self._notif_api or os.environ.get(
            "NOTIFICATIONS_API", "https://notif.naas.ai"
        )

    @notif_api.setter
    def notif_api(self, notif_api):
        self._notif_api = notif_api

    @property
    def callback_api(self):
        return self._callback_api or os.environ.get(
            "CALLBACK_API", "https://callback.naas.ai"
        )

    @callback_api.setter
    def callback_api(self, callback_api):
        self._callback_api = callback_api

    @property
    def report_callback(self):
        return self._report_callback or (
            os.environ.get("REPORT_CALLBACK", "True") == "True"
        )

    @report_callback.setter
    def report_callback(self, report_callback):
        self._report_callback = report_callback

    @property
    def proxy_api(self):
        if self.user and self.user != "":
            return self._proxy_api or os.environ.get(
                "PROXY_API", "https://public.naas.ai"
            )
        else:
            return f"{self.user_url}/naas"

    @proxy_api.setter
    def proxy_api(self, proxy_api):
        self._proxy_api = proxy_api

    @property
    def hub_base(self):
        res = (
            self._hub_base or os.environ.get("JUPYTERHUB_URL") or "https://app.naas.ai"
        )
        if "://" not in res:
            return f"http://{res}"
        else:
            return res

    @hub_base.setter
    def hub_base(self, hub_base):
        self._hub_base = hub_base

    @property
    def any_user_url(self):
        if self.user and self.user != "":
            base_url = f"{self.hub_base}/user-redirect"
        else:
            base_url = self.hub_base
        return base_url

    @property
    def user_url(self):
        if self.user and self.user != "":
            base_url = f"{self.hub_base}/user/{self.user}"
        else:
            base_url = self.hub_base
        return base_url

    @property
    def naas_folder(self):
        return self._naas_folder or os.environ.get("NAAS_FOLDER", ".naas")

    @naas_folder.setter
    def naas_folder(self, naas_folder):
        self._naas_folder = naas_folder

    @property
    def server_root(self):
        return self._server_root or os.environ.get(
            "JUPYTER_SERVER_ROOT", str(Path.home())
        )

    @server_root.setter
    def server_root(self, server_root):
        self._server_root = server_root

    @property
    def custom_path(self):
        return self._custom_path or os.environ.get("NAAS_CUSTOM_FOLDER", "/etc/naas")

    @custom_path.setter
    def custom_path(self, custom_path):
        self._custom_path = custom_path

    @property
    def path_naas_folder(self):
        return os.path.join(self.server_root, self.naas_folder)

    @property
    def shell_user(self):
        return self._shell_user or os.environ.get("NB_USER", "ftp")

    @shell_user.setter
    def shell_user(self, shell_user):
        self._shell_user = shell_user

    @property
    def remote_api(self):
        return f"{self.proxy_api}/runner"

    @property
    def token(self):
        return (
            self._token
            or os.environ.get("JUPYTERHUB_API_TOKEN", None)
            or os.environ.get("JUPYTER_TOKEN", "")
        )

    @token.setter
    def token(self, token):
        self._token = token

    @property
    def user(self):
        return self._user or os.environ.get("JUPYTERHUB_USER", "")

    @user.setter
    def user(self, user):
        self._user = user

    @property
    def tz(self):
        return self._tz or os.environ.get("TZ", str(get_localzone()))

    @tz.setter
    def tz(self, tz):
        self._tz = tz

    @property
    def sentry_dsn(self):
        return self._sentry_dsn or os.environ.get("NAAS_SENTRY_DSN", None)

    @sentry_dsn.setter
    def sentry_dsn(self, sentry_dsn):
        self._sentry_dsn = sentry_dsn

    @property
    def scheduler(self):
        return bool(self._scheduler)

    @scheduler.setter
    def scheduler(self, scheduler):
        self._scheduler = bool(scheduler)

    @property
    def scheduler_interval(self):
        return int(
            self._scheduler_interval or os.environ.get("NAAS_SCHEDULER_INTERVAL", "60")
        )

    @scheduler_interval.setter
    def scheduler_interval(self, scheduler_interval: int):
        self._scheduler_interval = scheduler_interval

    @property
    def scheduler_job_max(self):
        return int(
            self._scheduler_job_max or os.environ.get("NAAS_SCHEDULER_JOB_MAX", "60")
        )

    @scheduler_job_max.setter
    def scheduler_job_max(self, scheduler_job_max: int):
        self._scheduler_job_max = scheduler_job_max

    @property
    def scheduler_job_name(self):
        return self._scheduler_job_name or os.environ.get(
            "NAAS_SCHEDULER_JOB_NAME", "_scheduler_job"
        )

    @scheduler_job_name.setter
    def scheduler_job_name(self, scheduler_job_name):
        self._scheduler_job_name = scheduler_job_name

    @property
    def scheduler_timeout(self):
        return int(
            self._scheduler_timeout or os.environ.get("NAAS_SCHEDULER_TIMEOUT", "3600")
        )

    @scheduler_timeout.setter
    def scheduler_timeout(self, scheduler_timeout: int):
        self._scheduler_timeout = scheduler_timeout


n_env = n_env()


def cpath(path):
    return path.replace(n_env.path_naas_folder, "").replace(f"{n_env.server_root}/", "")
