from naas.types import t_notebook, t_scheduler, t_asset
from .proxy import encode_proxy_url
from .env_var import n_env
from bs4 import BeautifulSoup
import pandas as pd
import pretty_cron
import requests
import base64
import json
import uuid
import os


class Notifications:
    logger = None

    headers = None

    def __init__(self, logger=None):
        self.headers = {"Authorization": f"token {n_env.token}"}
        self.logger = logger

    def send(self, email_to, subject, html, files=[], email_from=None):
        uid = str(uuid.uuid4())
        soup = BeautifulSoup(html, features="html5lib")
        content = soup.get_text()
        try:
            data = {
                "subject": subject,
                "from": email_from,
                "email": ",".join(email_to) if isinstance(email_to, list) else email_to,
                "content": content,
                "html": html,
            }
            req = None
            if len(files) > 0:
                files_list = []
                for file in files:
                    abs_path = os.path.abspath(os.path.join(os.getcwd(), file))
                    try:
                        files_list.append((file, open(abs_path, "rb")))
                    except Exception as err:
                        print(err)
                req = requests.post(
                    url=f"{n_env.notif_api}/send",
                    files=files_list,
                    headers=self.headers,
                    data=data,
                )
            else:
                req = requests.post(
                    url=f"{n_env.notif_api}/send", headers=self.headers, json=data
                )
            req.raise_for_status()
            print("👌 💌 Email has been sent successfully !")
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps({"id": uid, "type": "email error", "error": str(err)})
                )
            else:
                print(err)

    def send_status(
        self,
        uid,
        status,
        email_to,
        file_path,
        current_type,
        current_value,
        files=[],
        email_from=None,
    ):
        if n_env.notif_api is None:
            jsn = {"id": uid, "type": "notification error", "error": "not configured"}
            if self.logger is not None:
                self.logger.error(json.dumps(jsn))
            else:
                print(jsn)
            return jsn
        content = ""
        file_link = f"{n_env.hub_api}/user/{n_env.user}/tree/{file_path}"
        if current_type == t_asset or current_type == t_notebook:
            content = f'The file <a href="{file_link}">{file_path}</a> <br/>'
            content += f"Accesible at this url:<br/> {encode_proxy_url(current_type)}/{current_value}<br/>"
        elif current_type == t_scheduler:
            cron_string = pretty_cron.prettify_cron(current_value)
            content = f'The file <a href="{file_link}">{file_path}</a><br/>'
            content += f"who run {cron_string}<br/>"
        content += f"Is {status}.<br/><br/>"
        content += "Check the Logs on your manager below :<br/>"
        status_url = f"{encode_proxy_url(t_asset)}/naas_{status}.png"
        message_bytes = file_path.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        file_path_base64 = base64_bytes.decode("ascii")
        link_url = f"{n_env.hub_api}/user/{n_env.user}/naas/?filter={file_path_base64}"
        logo_url = f"{encode_proxy_url(t_asset)}/naas_logo.png"
        try:
            data = {
                "title": "Naas manager notification",
                "subject": f"{current_type.capitalize()} {status}",
                "from": email_from,
                "email": ",".join(email_to) if isinstance(email_to, list) else email_to,
                "content": content,
                "custom_vars": {
                    "URL_HOME": encode_proxy_url(),
                    "URL_LOGO": logo_url,
                    "ALT_LOGO": "Naas Manager LOGO",
                    "URL_IMAGE": status_url,
                    "ALT_IMAGE": status,
                    "URL_LINK": link_url,
                },
            }
            req = None
            if len(files) > 0:
                files = {}
                for file in files:
                    abs_path = os.path.abspath(os.path.join(os.getcwd(), file))
                    try:
                        files[file] = open(abs_path, "rb")
                    except Exception as err:
                        print(err)
                req = requests.post(
                    url=f"{n_env.notif_api}/send_status",
                    headers=self.headers,
                    files=files,
                    json=data,
                )
            else:
                req = requests.post(
                    url=f"{n_env.notif_api}/send_status",
                    headers=self.headers,
                    json=data,
                )
            req.raise_for_status()
            jsn = req.json()
            return jsn
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps(
                        {"id": uid, "type": "notification error", "error": str(err)}
                    )
                )
            else:
                print(err)

    def status(self):
        req = requests.get(url=f"{n_env.notif_api}/")
        req.raise_for_status()
        jsn = req.json()
        return jsn

    def list(self):
        req = requests.post(
            url=f"{n_env.notif_api}/list",
            headers=self.headers,
        )
        jsn = req.json()
        return pd.DataFrame(data=jsn.get("emails"))

    def list_all(self):
        req = requests.post(
            url=f"{n_env.notif_api}/list_all",
            headers=self.headers,
        )
        jsn = req.json()
        return pd.DataFrame(data=jsn.get("emails"))
