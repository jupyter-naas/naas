from .types import t_scheduler
from .manager import Manager
import pretty_cron

class Refresh():
    naas = None
    role = t_scheduler

    def __init__(self):
        self.manager = Manager()

    def current_raw(self):
        json_data = self.manager.get_naas()
        for item in json_data:
            if item['type'] == self.role:
                print(item)
    
    def currents(self):
        json_data = self.manager.get_naas()
        for item in json_data:
            kind = None
            if item['type'] == self.role:
                cron_string = pretty_cron.prettify_cron(item['value'])
                kind = f"refresh {cron_string}"
                print(f"File ==> {item['path']} is {kind}")

    def add(self, path=None, reccurence=None, params=None, silent=False):
        if not self.manager.notebook_path():
            print(
                f'No add done you are in already in naas folder\n')
            return
        if not reccurence:
            print(
                f'No reccurence provided\n')
            return
        cron_string = pretty_cron.prettify_cron(reccurence)
        current_file = self.manager.get_path(path)
        prod_path = self.manager.get_prod_path(current_file)
        if silent is False:
            print(
                f'[Naas from Jupyter] => i have copied this {current_file} here: {prod_path} \n')
            print(f'it will refresh it {cron_string}\n')
            print(
                f'If you want to remove the refresh capability, just call .delete({path if path is not None else "" })) in this file')
        return self.manager.add_prod({"type": self.role, "path": current_file, "params": {}, "value": reccurence}, silent)

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
            print(
                f'No histo provided\n')
            return     
        current_file = self.manager.get_path(path)
        self.manager.get_history(current_file, histo)

    def list_history(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.list_history(current_file)
        
    def clear_history(self, path=None, histo=None):
        current_file = self.manager.get_path(path)
        self.manager.clear_history(current_file, histo)
        
    def delete(self, path=None, all=False, silent=False):
        if not self.manager.notebook_path():
            print(
                f'No delete done you are in already in naas folder\n')
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, silent)
        if all is True:
            self.manager.clear_history(current_file)
            self.manager.clear_output(current_file) 
    
    def help(self):
        print(f'=== {type(self).__name__} === \n')
        print(f'.add(path, params) => add path to the prod {type(self).__name__} server\n')
        print(f'.delete(path) => delete path to the prod {type(self).__name__} server\n')
        print('.clear_history(histonumber, path) => clear history, history number and path are optionel, if you don\'t provide them it will erase full history of current file \n')
        print('.list_history(path) => list history, of a path or if not provided the current file \n')
        print('.get_history(histonumber, path) => get history file, of a path or if not provided the current file \n')
        print('.get(path) => get current prod file of a path, or if not provided the current file \n')
        print(f'.currents() => get current list of {type(self).__name__} prod file\n')
        print(f'.current_raw() => get json current list of {type(self).__name__} prod file\n')