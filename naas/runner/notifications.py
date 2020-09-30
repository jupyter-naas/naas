from naas.types import t_notebook, t_scheduler, t_asset
from .proxy import encode_proxy_url
import pretty_cron
import requests
import base64
import json
import os
import uuid


class Notifications:
    logger = None
    base_notif_url = os.environ.get("NOTIFICATIONS_API", None)

    def __init__(self, logger=None):
        self.logger = logger

    def send(self, email, subject, content, html=None):
        uid = str(uuid.uuid4())
        if self.base_notif_url is None:
            jsn = {"id": uid, "type": "email error", "error": "not configured"}
            if self.logger is not None:
                self.logger.error(json.dumps(jsn))
            else:
                print(jsn)
            return jsn
        try:
            data = {
                "subject": subject,
                "email": email,
                "content": content,
                "html": html,
            }
            req = requests.post(url=f"{self.base_notif_url}/send", json=data)
            req.raise_for_status()
            jsn = req.json()
            return jsn
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps({"id": uid, "type": "email error", "error": str(err)})
                )
            else:
                print(err)

    def send_status(self, uid, status, email, file_path, current_type, current_value):
        if self.base_notif_url is None:
            jsn = {"id": uid, "type": "notification error", "error": "not configured"}
            if self.logger is not None:
                self.logger.error(json.dumps(jsn))
            else:
                print(jsn)
            return jsn
        content = ""
        if current_type == t_asset or current_type == t_notebook:
            content = f"The file {file_path} accesible at this url:<br/> {encode_proxy_url(current_type)}/{current_value}<br/>"
            content = content + f"is {status}.<br/><br/>"
            content = content + "Check the Logs on your manager below :<br/>"
        elif current_type == t_scheduler:
            cron_string = pretty_cron.prettify_cron(current_value)
            content = f"Your {file_path} who run {cron_string} is {status}, check the Logs on your manager below :"

        status_url = f"{encode_proxy_url(t_asset)}/naas_{status}.png"
        message_bytes = file_path.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        file_path_base64 = base64_bytes.decode("ascii")
        link_url = f"{encode_proxy_url()}/?filter={file_path_base64}"
        logo_url = f"{encode_proxy_url(t_asset)}/naas_logo.png"
        try:
            data = {
                "title": "Naas manager notification",
                "subject": f"{current_type.capitalize()} {status}",
                "email": email,
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
            req = requests.post(url=f"{self.base_notif_url}/send_status", json=data)
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

    def get_status_server(self):
        req = requests.get(url=f"{self.base_notif_url}/")
        req.raise_for_status()
        jsn = req.json()
        return jsn
