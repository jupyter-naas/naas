# Copyright (c) Naas Team.
# Distributed under the terms of the Modified BSD License.
from .scheduler import Scheduler
from .api import Api
from .assets import Assets
from .dependency import Dependency
from IPython.core.display import display, HTML
from .secret import Secret
from .runner import Runner
from .runner.notifications import Notifications
from .runner.proxy import encode_proxy_url
import requests
import os

__version__ = "0.7.1"
__location__ = os.getcwd()
scheduler = Scheduler()
secret = Secret()
runner = Runner()
api = Api()
assets = Assets()
dependency = Dependency()
notifications = Notifications()


def manager():
    public_url = f"{encode_proxy_url()}"
    print("You can check your current tasks list here :")
    display(HTML(f'<a href="{public_url}"">Manager</a>'))


def clean_logs():
    req = requests.get(url="localhost:5000/logs")
    req.raise_for_status()
    jsn = req.json()
    print(jsn)
    return jsn


def scheduler_status():
    req = requests.get(url="localhost:5000/scheduler")
    req.raise_for_status()
    jsn = req.json()
    print(jsn)
    return jsn


def scheduler_pause():
    req = requests.get(url="localhost:5000/scheduler/pause")
    req.raise_for_status()
    jsn = req.json()
    print(jsn)
    return jsn


def scheduler_resume():
    req = requests.get(url="localhost:5000/scheduler/resume")
    req.raise_for_status()
    jsn = req.json()
    print(jsn)
    return jsn


def welcome():
    print("[Nass from JupyterHub] => Welcome to your ETL, read the documentation")
    print("Do naas.help() to get more info on what you can do.\n")


def help():
    print("naas.version() => Get the current version\n")
    print("naas.manager() => Get the url of the manager\n")
    print("naas.scheduler => Get the notebook scheduler driver\n")
    print("naas.api => Get the notebook api driver\n")
    print("naas.assets => Get the file sharing driver\n")
    print("naas.dependency => Get the file dependency driver\n")
