from .types import t_secret, t_add
from .runner.env_var import n_env
import pandas as pd
import requests
import base64


class Secret:
    def list(self):
        try:
            r = requests.get(f"{n_env.api}/{t_secret}")
            r.raise_for_status()
            res = r.json()
            return pd.DataFrame.from_records(res)
        except requests.exceptions.ConnectionError as err:
            print(self.__error_manager_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_manager_reject, err)
            raise

    def add(self, name=None, secret=None):
        message_bytes = secret.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        secret_base64 = base64_bytes.decode("ascii")
        obj = {"name": name, "secret": secret_base64, "status": t_add}
        try:
            r = requests.post(f"{n_env.api}/{t_secret}", json=obj)
            r.raise_for_status()
            print("👌 Well done! Your Secret has been sent to production. \n")
            print('PS: to remove the "Secret" feature, just replace .add by .delete')
        except requests.exceptions.ConnectionError as err:
            print(self.__error_manager_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_manager_reject, err)
            raise

    def get(self, name=None, default_value=None):
        all_secret = self.list()
        secret_item = None
        for item in all_secret:
            if name == item["name"]:
                secret_item = item
                break
        if secret_item is not None:
            secret_base64 = secret_item.get("secret", None)
            if secret_base64 is not None:
                secret = base64.b64decode(secret_base64)
                return secret.decode("ascii")
        return default_value

    def delete(self, name=None):
        new_obj = []
        found = False
        json_data = self.__get_all()
        for item in json_data:
            if name != item["name"]:
                new_obj.append(item)
            else:
                found = True
        if len(json_data) != len(new_obj):
            self.__set_secret(new_obj)
        if found:
            print("Deleted =>>", name)
        else:
            print("Not found =>>", name)
        return None
