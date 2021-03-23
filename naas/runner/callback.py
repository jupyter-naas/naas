from naas.runner.env_var import n_env
from naas.types import copy_button
import pandas as pd
import requests
import time
import json


class Callback:
    logger = None

    headers = None

    def __init__(self, logger=None):
        #         n_env.callback_api = "http://naas-callback:3004"
        self.headers = {"Authorization": f"token {n_env.token}"}
        self.logger = logger

    def add(self, response={}, response_headers={}, auto_delete=True, default_result=None, no_override=False, user=None, uuid=None):
        try:
            data = {
                "response": response,
                "autoDelete": auto_delete,
                "responseHeaders": response_headers,
            }
            if no_override:
                data['responseHeaders']['naas_no_override'] = no_override
            if default_result:
                data['result'] = default_result
            if user:
                data['user'] = user
            if uuid:
                data['uuid'] = uuid
            req = requests.post(
                url=f"{n_env.callback_api}/", headers=self.headers, json=data
            )
            req.raise_for_status()
            jsn = req.json()
            print("👌 🔙 Callback has been created successfully !")
            url = f"{n_env.callback_api}/{jsn.get('uuid')}"
            copy_button(url)
            return {"url": url, "uuid": jsn.get("uuid")}
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps({"id": None, "type": "email error", "error": str(err)})
                )
            else:
                print(err)

    def __get(self, uuid, user=None):
        try:
            data = {
                "uuid": uuid,
            }
            if user:
                data['user'] = user
            req = requests.get(
                url=f"{n_env.callback_api}/",
                params=data,
                headers=self.headers,
            )
            req.raise_for_status()
            jsn = req.json()
            return jsn
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps({"id": uuid, "type": "email error", "error": str(err)})
                )
            else:
                print(err)

    def get(self, uuid, wait_until_data=False, timeout=3000, raw=False, user=None):
        data = None
        total = 0
        while data is None or data.get("result") is None:
            if total > timeout:
                print("🥲 Callback Get timeout !")
                return None
            data = self.__get(uuid, user)
            time.sleep(1)
            total += 1
            if wait_until_data:
                break
        if data and data.get("result") and data.get("result") != "":
            print("👌 🔙 Callback has been trigger, here your data !")
        else:
            print("🥲 Callback is empty !")
        return data if raw else data.get("result")

    def delete(self, uuid, user=None):
        try:
            data = {
                "uuid": uuid,
            }
            if user:
                data['user'] = user
            req = requests.delete(
                url=f"{n_env.callback_api}/", headers=self.headers, json=data
            )
            req.raise_for_status()
            print("👌 🔙 Callback has been delete successfully !")
            return
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps({"id": uuid, "type": "email error", "error": str(err)})
                )
            else:
                print(err)

    def status(self):
        req = requests.get(url=f"{n_env.callback_api}/")
        req.raise_for_status()
        jsn = req.json()
        return jsn

    def list(self):
        req = requests.get(
            url=f"{n_env.callback_api}/",
            headers=self.headers,
        )
        req.raise_for_status()
        jsn = req.json()
        return pd.DataFrame(data=jsn.get("callbacks"))

    def list_all(self):
        req = requests.get(
            url=f"{n_env.callback_api}/admin",
            headers=self.headers,
        )
        req.raise_for_status()
        jsn = req.json()
        return pd.DataFrame(data=jsn.get("callbacks"))
