from .ntypes import (
    copy_button_df,
    copy_clipboard,
    t_asset,
    copy_button,
    t_add,
    t_update,
    t_delete,
)
from .manager import Manager
import pandas as pd
import warnings
import os


class Assets:
    naas = None
    manager = None
    role = t_asset
    deprecated_name = False

    def __init__(self, deprecated_name=False):
        self.manager = Manager(t_asset)
        self.path = self.manager.path
        self.deprecated_name = deprecated_name

    def deprecatedPrint(self):
        # TODO remove this in june 2021
        if self.deprecated_name:
            warnings.warn(
                "[Warning], naas.assets is deprecated,\n use naas.asset instead, it will be remove in 1 june 2021"
            )

    def list(self, path=None):
        self.deprecatedPrint()
        return self.manager.list_prod("list_history", path)

    def get(self, path=None, histo=None):
        self.deprecatedPrint()
        return self.manager.get_file(path, histo=histo)

    def clear(self, path=None, histo=None):
        self.deprecatedPrint()
        return self.manager.clear_file(path, None, histo)

    def currents(self, raw=False):
        self.deprecatedPrint()
        copy_clipboard()
        json_data = self.manager.get_naas()
        json_filtered = []
        for item in json_data:
            if item["type"] == self.role and item["status"] != t_delete:
                if raw:
                    json_filtered.append(item)
                else:
                    json_filtered.append(
                        {
                            "path": item["path"],
                            "url": self.manager.proxy_url("assets", item["value"]),
                        }
                    )
        if raw is False:
            df = pd.DataFrame(json_filtered)
            df = df.style.format({"url": copy_button_df})
            return df
        return json_filtered

    def find(self, path=None):
        self.deprecatedPrint()
        current_file = self.manager.get_path(path)
        if current_file is None:
            print("Missing file path")
            return
        try:
            token = self.manager.get_value(current_file, False)
            return self.manager.proxy_url(self.role, token)
        except:  # noqa: E722
            return None

    def add(
        self, path=None, params={}, debug=False, force_image=False, override_prod=False
    ):
        self.deprecatedPrint()
        current_file = self.manager.get_path(path)
        if current_file is None:
            print("Missing file path")
            return
        token = os.urandom(30).hex()
        if current_file.endswith(".png") or force_image:
            token = f"{token}.png"
        status = t_add
        try:
            token = self.manager.get_value(current_file, False)
            status = t_update
        except:  # noqa: E722
            pass
        url = self.manager.proxy_url(self.role, token)
        if self.manager.is_production():
            if override_prod is False:
                print("No add done, you are in production\n")
                return None
            else:
                if os.path.exists(current_file) is False:
                    current_file = os.path.join(os.getcwd(), path)
                print("Adding assets to production anyway.")
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

    def delete(self, path=None, all=True, debug=False):
        self.deprecatedPrint()
        if self.manager.is_production():
            print("No delete done, you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Assets has been remove from production.\n")
        if all is True:
            self.clear(current_file, "all")
