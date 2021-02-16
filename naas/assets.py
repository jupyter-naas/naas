from .types import t_asset, copy_button, t_add, t_update, t_delete
from .runner.env_var import n_env
from .manager import Manager
import os


class Assets:
    naas = None
    manager = None
    role = t_asset

    def __init__(self):
        self.manager = Manager(t_asset)
        self.path = self.manager.path

    def list(self, path=None):
        return self.manager.list_prod("list_history", path)

    def get(self, path=None, histo=None):
        return self.manager.get_file(path, histo=histo)

    def clear(self, path=None, histo=None):
        return self.manager.clear_file(path, None, histo)

    def currents(self, raw=False):
        json_data = self.manager.get_naas()
        if raw:
            json_filtered = []
            for item in json_data:
                if item["type"] == self.role and item["status"] != t_delete:
                    print(item)
                    json_filtered.append(item)
                return json_filtered
        else:
            for item in json_data:
                kind = None
                if item["type"] == self.role and item["status"] != t_delete:
                    kind = f"gettable with this url {self.manager.proxy_url('assets', item['value'])}"
                    path = (
                        item["path"]
                        .replace(n_env.path_naas_folder, "")
                        .replace(n_env.server_root, "")
                    )
                    print(f"File ==> {path} is {kind}")

    def add(self, path=None, params={}, debug=False):
        current_file = self.manager.get_path(path)
        if current_file is None:
            print("Missing file path in prod mode")
            return
        token = os.urandom(30).hex()
        status = t_add
        try:
            token = self.manager.get_value(current_file, False)
            status = t_update
        except:  # noqa: E722
            pass
        url = self.manager.proxy_url(self.role, token)
        if self.manager.is_production():
            print("No add done, you are in production\n")
            return url
        # "path", "type", "params", "value", "status"
        self.manager.add_prod(
            {
                "type": self.role,
                "status": status,
                "path": current_file,
                "params": params,
                "value": token,
            },
            debug,
        )
        print("👌 Well done! Your Assets has been sent to production.\n")
        copy_button(url)
        print('PS: to remove the "Assets" feature, just replace .add by .delete')
        return url

    def delete(self, path=None, all=False, debug=False):
        if self.manager.is_production():
            print("No delete done, you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Assets has been remove from production.\n")
        if all is True:
            self.clear(path)
