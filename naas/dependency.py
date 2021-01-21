from .types import t_dependency
from .manager import Manager


class Dependency:
    naas = None
    role = t_dependency
    manager = None

    def __init__(self):
        self.manager = Manager(t_dependency)
        self.path = self.manager.path

    def list(self, path=None):
        return self.manager.list_prod(None, path)

    def get(self, path=None):
        return self.manager.get_file(path)

    def clear(self, path=None, histo=None):
        return self.manager.clear_file(path, None, histo)

    def currents(self, raw=False):
        json_data = self.manager.get_naas()
        if raw:
            for item in json_data:
                if item["type"] == self.role:
                    print(item)
        else:
            for item in json_data:
                if item["type"] == self.role:
                    print(f"File ==> {item['path']}")

    def add(self, path=None, debug=False):
        if self.manager.is_production():
            print("No add done you are in production\n")
            return self.get_path(path)
        current_file = self.manager.get_path(path)
        self.manager.add_prod(
            {
                "type": self.role,
                "path": current_file,
                "params": {},
                "value": "Only internal",
            },
            debug,
        )
        print("👌 Well done! Your Dependency has been sent to production. \n")
        print('PS: to remove the "Dependency" feature, just replace .add by .delete')
        return self.get_path(current_file)

    def delete(self, path=None, all=False, debug=False):
        if self.manager.is_production():
            print("No delete done you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Dependency has been remove from production.\n")
        if all is True:
            self.clear(path)
