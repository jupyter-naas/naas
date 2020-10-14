from .types import t_asset
from .manager import Manager
import os


class Assets:
    naas = None
    role = t_asset

    def __init__(self):
        self.manager = Manager()
        self.list = self.manager.list_prod
        self.clear = self.manager.clear_prod
        self.get = self.manager.get_prod
        self.get_output = self.manager.get_output
        self.clear_output = self.manager.clear_output

    def current_raw(self):
        json_data = self.manager.get_naas()
        for item in json_data:
            if item["type"] == self.role:
                print(item)

    def currents(self, raw=False):
        json_data = self.manager.get_naas()
        if raw:
            for item in json_data:
                if item["type"] == self.role:
                    print(item)
        else:
            for item in json_data:
                kind = None
                if item["type"] == self.role:
                    kind = f"gettable with this url {self.manager.proxy_url('assets', item['value'])}"
                    print(f"File ==> {item['path']} is {kind}")

    def add(self, path=None, params={}, debug=False, force=False):
        current_file = self.manager.get_path(path)
        if current_file is None:
            print("Missing file path in prod mode")
            return
        prod_path = self.manager.get_prod_path(current_file)
        token = self.manager.get_value(prod_path, self.role)
        if token is None or force is True:
            token = os.urandom(30).hex()
        url = self.manager.proxy_url(self.role, token)
        if self.manager.is_production() and force is False:
            print("No add done you are in production\n")
            return url
        # "path", "type", "params", "value", "status"
        self.manager.add_prod(
            {"type": self.role, "path": current_file, "params": params, "value": token},
            debug,
        )
        print("👌 Well done! Your Assets has been sent to production.\n")
        self.manager.copy_url(url)
        print('PS: to remove the "Assets" feature, just replace .add by .delete')
        return url

    def delete(self, path=None, all=False, debug=False):
        if self.manager.is_production():
            print("No delete done you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Assets has been remove from production.\n")
        if all is True:
            self.clear(path)
