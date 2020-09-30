from .types import t_scheduler
from .manager import Manager
import pretty_cron
import pycron


class Scheduler:
    naas = None
    role = t_scheduler

    def __init__(self):
        self.manager = Manager()

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
                    cron_string = pretty_cron.prettify_cron(item["value"])
                    kind = f"scheduler {cron_string}"
                    print(f"File ==> {item['path']} is {kind}")

    def __check_cron(self, text):
        res = False
        try:
            pycron.is_now(text)
            res = True
        except:  # noqa: E722
            pass
        return res

    def add(self, path=None, recurrence=None, params=None, debug=False):
        if not self.manager.notebook_path():
            print("No add done you are in already in naas folder\n")
            return
        if not recurrence:
            print("No recurrence provided\n")
            return
        if not self.__check_cron(recurrence):
            print(f"WARNING : Recurrence wrong format {recurrence}")
            return
        cron_string = pretty_cron.prettify_cron(recurrence)
        current_file = self.manager.get_path(path)
        print("👌 Well done! Your Notebook has been sent to production folder. \n")
        print(
            f'⏰ It will be scheduled "{cron_string}" (more on the syntax on https://crontab.guru/).\n'
        )
        print('Ps: to remove the "Scheduler", just replace .add by .delete')
        self.manager.add_prod(
            {
                "type": self.role,
                "path": current_file,
                "params": {},
                "value": recurrence,
            },
            not debug,
        )

    def get(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.get_prod(current_file)

    def clear_output(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.clear_output(current_file)

    def get_output(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.get_output(current_file)

    def get_history(self, path=None, histo=None):
        if not histo:
            print("No histo provided\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.get_history(current_file, histo)

    def list_history(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.list_history(current_file)

    def clear_history(self, path=None, histo=None):
        current_file = self.manager.get_path(path)
        self.manager.clear_history(current_file, histo)
        print("🕣 Your Scheduler history has been remove from production folder.\n")

    def delete(self, path=None, all=False, debug=False):
        if not self.manager.notebook_path():
            print("No delete done you are in already in naas folder\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, not debug)
        print("🗑 Done! Your Scheduler has been remove from production folder.\n")
        if all is True:
            self.manager.clear_history(current_file)
            self.manager.clear_output(current_file)

    def help(self):
        print(f"=== {type(self).__name__} === \n")
        print(
            f".add(path, params) => add path to the prod {type(self).__name__} server\n"
        )
        print(
            f".delete(path) => delete path to the prod {type(self).__name__} server\n"
        )
        print(
            ".clear_history(histonumber, path) => clear history, history number and path are optionel, \
                if you don't provide them it will erase full history of current file \n"
        )
        print(
            ".list_history(path) => list history, of a path or if not provided the current file \n"
        )
        print(
            ".get_history(histonumber, path) => get history file, of a path or if not provided the current file \n"
        )
        print(
            ".get(path) => get current prod file of a path, or if not provided the current file \n"
        )
        print(f".currents() => get current list of {type(self).__name__} prod file\n")
        print(
            f".current(raw=True) => get json current list of {type(self).__name__} prod file\n"
        )
