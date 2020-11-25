import pytest  # noqa: F401
import black  # noqa: F401  # FIX for https://github.com/psf/black/issues/1143
import os
import getpass
import logging
import sys
from datetime import datetime
from unittest.mock import Mock

print(sys.version_info)
if sys.version_info >= (3, 9):
    from zoneinfo import ZoneInfo
else:
    from backports.zoneinfo import ZoneInfo


@pytest.fixture(scope="session")
def timezone():
    return ZoneInfo("Europe/Paris")


@pytest.fixture
def freeze_time(monkeypatch, timezone):
    class TimeFreezer:
        def __init__(self, initial):
            self.current = initial
            self.increment = None

        def get(self, tzinfo=None):
            now = (
                self.current.astimezone(tzinfo)
                if tzinfo
                else self.current.replace(tzinfo=None)
            )
            if self.increment:
                self.current += self.increment
            return now

        def set(self, new_time):
            self.current = new_time

        def next(
            self,
        ):
            return self.current + self.increment

        def set_increment(self, delta):
            self.increment = delta

    freezer = TimeFreezer(timezone.localize(datetime(2011, 4, 3, 18, 40)))
    fake_datetime = Mock(datetime, now=freezer.get)
    monkeypatch.setattr("apscheduler.triggers.interval.datetime", fake_datetime)
    monkeypatch.setattr("apscheduler.triggers.date.datetime", fake_datetime)
    return freezer


user_folder_name = "pytest_tmp"
path_srv_root = os.path.join(os.getcwd(), user_folder_name)
os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
os.environ["NAAS_SCHEDULER_TIME"] = "1"
os.environ["NAAS_SCHEDULER_INSTANCE_MAX"] = "3"
os.environ["JUPYTERHUB_URL"] = "http://localhost:5000"
os.environ["PUBLIC_PROXY_API"] = "http://localhost:5001"
os.environ["NOTIFICATIONS_API"] = "http://localhost:5002"


@pytest.fixture
def runner(caplog, tmp_path):
    caplog.set_level(logging.INFO)
    user = getpass.getuser()
    path_srv_root = os.path.join(tmp_path, user_folder_name)
    os.environ["JUPYTER_SERVER_ROOT"] = str(path_srv_root)
    os.environ["JUPYTERHUB_USER"] = user

    from naas.runner import Runner  # noqa: E402

    app = Runner().init_app()

    yield app


@pytest.fixture
def test_cli(loop, runner, sanic_client):
    return loop.run_until_complete(sanic_client(runner))
