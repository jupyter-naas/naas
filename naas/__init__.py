# Copyright (c) Naas Team.
# Distributed under the terms of the GNU AGPL License.
from IPython.core.display import display, Javascript, HTML
from .runner.notifications import Notifications
from .runner.proxy import Domain
from .dependency import Dependency
from .scheduler import Scheduler
import ipywidgets as widgets
from .assets import Assets
from .secret import Secret
from .runner import Runner
from .api import Api
import requests
import os

__version__ = "0.20.0b0"
__github_repo = "jupyter-naas/naas"
__doc_url = "https://naas.gitbook.io/naas/"
__cannyjs = '<script>!function(w,d,i,s){function l(){if(!d.getElementById(i)){var f=d.getElementsByTagName(s)[0],e=d.createElement(s);e.type="text/javascript",e.async=!0,e.src="https://canny.io/sdk.js",f.parentNode.insertBefore(e,f)}}if("function"!=typeof w.Canny){var c=function(){c.q.push(arguments)};c.q=[],w.Canny=c,"complete"===d.readyState?l():w.attachEvent?w.attachEvent("onload",l):w.addEventListener("load",l,!1)}}(window,document,"canny-jssdk","script");</script>'  # noqa: E501
__location__ = os.getcwd()
scheduler = Scheduler()
secret = Secret()
runner = Runner()
api = Api()
assets = Assets()
dependency = Dependency()
notifications = Notifications()
Domain = Domain()


def version():
    print(__version__)


def get_last_version():
    url = f"https://api.github.com/repos/{__github_repo}/tags"
    response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
    return response.json()[0]["name"]


def changelog():
    data = __cannyjs
    data += """<button class="lm-Widget p-Widget jupyter-widgets jupyter-button widget-button mod-primary" data-canny-changelog>
        View Changelog
    </button>"""
    data += "<script> Canny('initChangelog', {appID: '5f81748112b5d73b2faf4b15', position: 'bottom', align: 'left'});</script>"
    display(HTML(data))


def bug_report():
    email = os.environ.get("JUPYTERHUB_USER", None)
    name = email.split(".")[0]
    board_id = "6a83d5c5-2165-2608-082d-49959c7f030c"

    data = __cannyjs
    data += "<div data-canny />"
    data += """
    <script>
        Canny('identify', {
            appID: '5f81748112b5d73b2faf4b15',
            user: {
                email: "{EMAIL}",
                name: "{NAME}",
                created: new Date().toISOString()
            },
        });
        Canny('render', {
            boardToken: "{BOARD}",
        });
    </script>
    """

    data = data.replace("{EMAIL}", email)
    data = data.replace("{BOARD}", board_id)
    data = data.replace("{NAME}", name)
    display(HTML(data))


def feature_request():
    email = os.environ.get("JUPYTERHUB_USER", None)
    name = email.split(".")[0]
    board_id = "e3e3e0c3-7520-47f5-56f5-39182fb70480"

    data = __cannyjs
    data += "<div data-canny />"
    data += """
    <script>
        Canny('identify', {
            appID: '5f81748112b5d73b2faf4b15',
            user: {
                email: "{EMAIL}",
                name: "{NAME}",
                created: new Date().toISOString()
            },
        });
        Canny('render', {
            boardToken: "{BOARD}",
        });
    </script>
    """

    data = data.replace("{EMAIL}", email)
    data = data.replace("{BOARD}", board_id)
    data = data.replace("{NAME}", name)
    display(HTML(data))


def doc():
    button = widgets.Button(description="Open Doc", button_style="primary")
    output = widgets.Output()

    def on_button_clicked(b):
        with output:
            display(Javascript('window.open("{url}");'.format(url=__doc_url)))

    button.on_click(on_button_clicked)
    display(button, output)


def up_to_date():
    return get_last_version() == version()


def update():
    token = os.environ.get("JUPYTERHUB_API_TOKEN")
    username = os.environ.get("JUPYTERHUB_USER")
    api_url = f'{os.environ.get("JUPYTERHUB_URL", "https://app.naas.ai")}/hub/api'
    r = requests.delete(
        f"{api_url}/users/{username}/server",
        headers={
            "Authorization": f"token {token}",
        },
    )
    r.raise_for_status()
    return r


def auto_update():
    if not up_to_date():
        update()
    else:
        print("You are aready up to date")


def is_production():
    return api.manager.is_production()
