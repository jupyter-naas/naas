from .types import t_dependency, t_add, t_update, t_delete
from .runner.env_var import n_env
from .manager import Manager


class Dependency:
    naas = None
    role = t_dependency
    manager = None

    def __init__(self):
        self.manager = Manager(t_dependency)
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
                if item["type"] == self.role and item["status"] != t_delete:
                    path = (
                        item["path"]
                        .replace(n_env.path_naas_folder, "")
                        .replace(n_env.server_root, "")
                    )
                    print(f"File ==> {path}")

    def add(self, path=None, debug=False):
        if self.manager.is_production():
            print("No add done, you are in production\n")
            return self.manager.get_path(path)
        current_file = self.manager.get_path(path)
        status = t_add
        try:
            self.manager.get_value(current_file, False)
            status = t_update
        except:  # noqa: E722
            pass
        self.manager.add_prod(
            {
                "type": self.role,
                "status": status,
                "path": current_file,
                "params": {},
                "value": "Only internal",
            },
            debug,
        )
        print("👌 Well done! Your Dependency has been sent to production. \n")
        print('PS: to remove the "Dependency" feature, just replace .add by .delete')
        return self.manager.get_path(current_file)

    def delete(self, path=None, all=False, debug=False):
        if self.manager.is_production():
            print("No delete done, you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Dependency has been remove from production.\n")
        if all is True:
            self.clear(path)
