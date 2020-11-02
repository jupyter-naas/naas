# Copyright (c) Naas Team.
# Distributed under the terms of the GNU AGPL License.
from IPython.core.display import display, Javascript
from .runner.notifications import Notifications
from .dependency import Dependency
from .scheduler import Scheduler
import ipywidgets as widgets
from .assets import Assets
from .secret import Secret
from .runner import Runner
from .api import Api
import requests
import os

__version__ = "0.14.0"
__github_repo = "jupyter-naas/naas"
__doc_url = "https://naas.gitbook.io/naas/"
__location__ = os.getcwd()
scheduler = Scheduler()
secret = Secret()
runner = Runner()
api = Api()
assets = Assets()
dependency = Dependency()
notifications = Notifications()


def version():
    print(__version__)


def get_last_version():
    url = f"https://api.github.com/repos/{__github_repo}/tags"
    response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
    return response.json()[0]["name"]


def doc():
    button = widgets.Button(description="Open Doc")
    output = widgets.Output()

    def on_button_clicked(b):
        with output:
            display(Javascript('window.open("{url}");'.format(url=__doc_url)))

    button.on_click(on_button_clicked)
    display(button, output)


def up_to_date():
    return get_last_version() == version()


def auto_update():
    if not up_to_date():
        update()


def update():
    os.system("kill -s SIGKILL 6")


def is_production():
    return api.manager.is_production()
