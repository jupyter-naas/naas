# Copyright (c) Naas Team.
# Distributed under the terms of the GNU AGPL License.
from .ntypes import t_tz, error_busy, error_reject, copy_button
from IPython.core.display import display, Javascript, HTML
from .runner.notifications import Notifications
from .dependency import Dependency
from .runner.env_var import n_env
from .runner.proxy import Domain
from .scheduler import Scheduler
from .callback import Callback
import ipywidgets as widgets
from .assets import Assets
from .secret import Secret
from .api import Api
import requests
import os
import sys

__version__ = "1.9.8"
__github_repo = "jupyter-naas/naas"
__doc_url = "https://naas.gitbook.io/naas/"
__canny_js = '<script>!function(w,d,i,s){function l(){if(!d.getElementById(i)){var f=d.getElementsByTagName(s)[0],e=d.createElement(s);e.type="text/javascript",e.async=!0,e.src="https://canny.io/sdk.js",f.parentNode.insertBefore(e,f)}}if("function"!=typeof w.Canny){var c=function(){c.q.push(arguments)};c.q=[],w.Canny=c,"complete"===d.readyState?l():w.attachEvent?w.attachEvent("onload",l):w.addEventListener("load",l,!1)}}(window,document,"canny-jssdk","script");</script>'  # noqa: E501
__crisp = '<script type="text/javascript">window.$crisp=[];window.CRISP_WEBSITE_ID="a64b999e-e44c-44ee-928f-5cd0233f9586";(function(){d=document;s=d.createElement("script");s.src="https://client.crisp.chat/l.js";s.async=1;d.getElementsByTagName("head")[0].appendChild(s);})();</script>'  # noqa: E501
__location__ = os.getcwd()

if len(sys.argv) == 0 or (len(sys.argv) > 0 and sys.argv[0] != "-m"):
    scheduler = Scheduler()
    secret = Secret()
    api = Api(True)
    webhook = Api()
    assets = Assets()
    dependency = Dependency()
    notifications = Notifications()
    callback = Callback()
    Domain = Domain()


def version():
    print(__version__)


n_env.version = __version__


def get_last_version():
    url = f"https://api.github.com/repos/{__github_repo}/tags"
    response = requests.get(url, headers={"Accept": "application/vnd.github.v3+json"})
    return response.json()[0]["name"]


def get_size():
    webhook.manager.get_size()


def reload_jobs():
    webhook.manager.reload_jobs()


def run(path=None, debug=False):
    return webhook.run(path, debug)


def move_job(old_path, new_path):
    webhook.manager.move_job(old_path, new_path)


def changelog():
    data = __canny_js
    data += """<button class="lm-Widget p-Widget jupyter-widgets jupyter-button widget-button mod-primary" data-canny-changelog>
        View Changelog
    </button>"""
    data += "<script> Canny('initChangelog', {appID: '5f81748112b5d73b2faf4b15', position: 'bottom', align: 'left'});</script>"
    display(HTML(data))


def open_help():
    data = __crisp
    data += (
        f'<script>$crisp.push(["set", "user:email", ["{str(n_env.user)}"]])</script>'
    )
    data += f'<script>$crisp.push(["set", "session:data", [[["naas_version", "{str(n_env.version)}"]]]])</script>'
    data += '<script>$crisp.push(["do", "chat:open"])</script>'
    display(HTML(data))


def close_help():
    data = '<script>$crisp.push(["do", "chat:hide"])</script>'
    display(HTML(data))


def bug_report():
    email = n_env.user
    name = email.split(".")[0]
    name = email.split("@")[0]
    board_id = "6a83d5c5-2165-2608-082d-49959c7f030c"

    data = __canny_js
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

    data = data.replace("{EMAIL}", str(n_env.user))
    data = data.replace("{BOARD}", board_id)
    data = data.replace("{NAME}", name)
    display(HTML(data))


def feature_request():
    email = str(n_env.user)
    name = email.split(".")[0]
    name = email.split("@")[0]
    board_id = "e3e3e0c3-7520-47f5-56f5-39182fb70480"

    data = __canny_js
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

    data = data.replace("{EMAIL}", str(n_env.user))
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
    username = n_env.user
    api_url = f"{n_env.hub_base}/hub/api"
    r = requests.delete(
        f"{api_url}/users/{username}/server",
        headers={
            "Authorization": f"token {n_env.token}",
        },
    )
    r.raise_for_status()
    return r


def auto_update():
    if not up_to_date():
        update()
    else:
        print("You are aready up to date")


def get_download_url(url):
    dl_url = f"{n_env.any_user_url}/naas/downloader?url={url}"
    print("❤️ Copy this url and spread it to the world\n")
    copy_button(dl_url)
    return dl_url


def is_production():
    return api.manager.is_production()


def remote_connect(user, token):
    n_env.token = token
    n_env.user = user


def get_remote_timezone():
    try:
        r = requests.get(f"{n_env.api}/{t_tz}")
        r.raise_for_status()
        res = r.json()
        print(f"🕣 Your Production Timezone is {res.get('tz')}\n")
        return res
    except requests.exceptions.ConnectionError as err:
        print(error_busy, err)
        raise
    except requests.exceptions.HTTPError as err:
        print(error_reject, err)
        raise


def set_remote_timezone(timezone):
    n_env.tz = timezone
    try:
        r = requests.post(f"{n_env.api}/{t_tz}", json={"tz": timezone})
        r.raise_for_status()
        res = r.json()
        print(f"🕣 Your Production Timezone is {res.get('tz')}\n")
        return res
    except requests.exceptions.ConnectionError as err:
        print(error_busy, err)
        raise
    except requests.exceptions.HTTPError as err:
        print(error_reject, err)
        raise
