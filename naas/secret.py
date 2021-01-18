from .types import t_secret, t_add, t_delete
from .runner.env_var import n_env
import pandas as pd
import requests


class Secret:

    __error_busy = "Naas look busy, try to reload your machine"
    __error_reject = "Naas refused your request, reason :"

    def list(self, raw=False):
        try:
            r = requests.get(f"{n_env.api}/{t_secret}")
            r.raise_for_status()
            res = r.json()
            if raw:
                return res
            else:
                return pd.DataFrame.from_records(res)
        except requests.exceptions.ConnectionError as err:
            print(self.__error_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_reject, err)
            raise

    def add(self, name=None, secret=None):
        obj = {"name": name, "secret": secret, "status": t_add}
        try:
            r = requests.post(f"{n_env.api}/{t_secret}", json=obj)
            r.raise_for_status()
            print("👌 Well done! Your Secret has been sent to production. \n")
            print('PS: to remove the "Secret" feature, just replace .add by .delete')
        except requests.exceptions.ConnectionError as err:
            print(self.__error_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_reject, err)
            raise

    def get(self, name=None, default_value=None):
        all_secret = self.list(True)
        secret_item = None
        for item in all_secret:
            if name == item["name"]:
                secret_item = item
                break
        if secret_item is not None:
            return secret_item.get("secret", None)
        return default_value

    def delete(self, name=None):
        obj = {"name": name, "secret": "", "status": t_delete}
        try:
            r = requests.post(f"{n_env.api}/{t_secret}", json=obj)
            r.raise_for_status()
            print("👌 Well done! Your Secret has been remove in production. \n")
        except requests.exceptions.ConnectionError as err:
            print(self.__error_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_reject, err)
            raise
