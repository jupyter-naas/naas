# Copyright (c) Naas Team.
# Distributed under the terms of the GNU AGPL License.

from .runner.notifications import Notifications
from .dependency import Dependency
from .scheduler import Scheduler
from .assets import Assets
from .secret import Secret
from .runner import Runner
from .api import Api
import os

__version__ = "0.10.1"
__location__ = os.getcwd()
scheduler = Scheduler()
secret = Secret()
runner = Runner()
api = Api()
assets = Assets()
dependency = Dependency()
notifications = Notifications()


def is_production():
    return api.manager.is_production()
