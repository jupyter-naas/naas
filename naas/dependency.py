from .types import t_dependency
from .manager import Manager


class Dependency:
    naas = None
    role = t_dependency

    def __init__(self):
        self.manager = Manager()
        self.get = self.manager.get_prod
        self.list = self.manager.list_prod
        self.clear = self.manager.clear_prod

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
        if not self.manager.notebook_path():
            print("No add done you are in already in naas folder\n")
            return
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
        print("👌 Well done! Your Dependency has been sent to production folder. \n")
        print('PS: to remove the "Dependency" feature, just replace .add by .delete')

    def delete(self, path=None, all=False, debug=False):
        if not self.manager.notebook_path():
            print("No delete done you are in already in naas folder\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Dependency has been remove from production folder.\n")
        if all is True:
            self.clear(path)

    def help(self):
        print(f"=== {type(self).__name__} === \n")
        print(".add(path) => add path to the prod server\n")
        print(
            f".delete(path) => delete path to the prod {type(self).__name__} server\n"
        )
        print(
            ".clear(path, histonumber) => clear history, history number and path are optionel, \
                if you don't provide them it will erase full history of current file \n"
        )
        print(
            ".list(path) => list history, of a path or if not provided the current file \n"
        )
        print(
            ".get(path, histonumber) => get prod file, of a path or if not provided the current file \n"
        )
        print(f".currents() => get current list of {type(self).__name__} prod file\n")
        print(
            f".current(raw=True) => get json current list of {type(self).__name__} prod file\n"
        )
