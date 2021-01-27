from naas.runner.env_var import n_env
import pandas as pd
import requests
import json


class Callback:
    logger = None

    headers = None

    def __init__(self, logger=None):
        #         n_env.callback_api = "http://naas-callback:3004"
        self.headers = {"Authorization": f"token {n_env.token}"}
        self.logger = logger

    def add(self, response=None, responseHeaders=None):
        try:
            data = {
                "response": response,
                "responseHeaders": responseHeaders,
            }
            req = None
            req = requests.post(
                url=f"{n_env.callback_api}/", headers=self.headers, json=data
            )
            req.raise_for_status()
            jsn = req.json()
            print("👌 🔙 Callback has been created successfully !")
            return {
                "url": f"{n_env.callback_api}/{jsn.get('uuid')}",
                "uuid": jsn.get("uuid"),
            }
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps({"id": None, "type": "email error", "error": str(err)})
                )
            else:
                print(err)

    def get(self, uuid, wait_until_data=False):
        try:
            data = {
                "uuid": uuid,
            }
            req = None
            req = requests.get(
                url=f"{n_env.callback_api}/",
                params={"uuid": uuid},
                headers=self.headers,
                json=data,
            )
            req.raise_for_status()
            jsn = req.json()
            if jsn and jsn.get("result") and jsn.get("result") != "":
                print("👌 🔙 Callback has been trigger, here your data !")
            else:
                print("🥲 Callback is empty !")
            return jsn
        except Exception as err:
            if self.logger is not None:
                self.logger.error(
                    json.dumps({"id": uuid, "type": "email error", "error": str(err)})
                )
            else:
                print(err)

    def delete(self, uuid):
        try:
            data = {
                "uuid": uuid,
            }
            req = None
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
