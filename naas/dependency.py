from .types import t_dependency
from .manager import Manager

class Dependency():  
    naas = None
    role = t_dependency

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
            if item['type'] == self.role:
                print(f"File ==> {item['path']}")

    def get(self, path=None):
        if not self.manager.notebook_path():
            print(
                f'No get done you are in already in naas folder\n')
            return  
        current_file = self.manager.get_path(path)
        self.manager.get_prod(current_file)

    def get_history(self, histo, path=None):
        if not self.manager.notebook_path():
            print(
                f'No get history done you are in already in naas folder\n')
            return  
        current_file = self.manager.get_path(path)
        self.manager.get_history(current_file, histo)

    def list_history(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.list_history(current_file)
        
    def clear_history(self, path=None, histo=None):
        if not self.manager.notebook_path():
            print(
                f'No clear history done you are in already in naas folder\n')
            return  
        current_file = self.manager.get_path(path)
        self.manager.clear_history(current_file, histo)
                
    def add(self, path=None, silent=False):
        if not self.manager.notebook_path():
            print(
                f'No add done you are in already in naas folder\n')
            return
        current_file = self.manager.get_path(path)
        prod_path = self.manager.get_prod_path(current_file)
        if silent is False:
            print(
                f'[Naas from Jupyter] => i have copied this {current_file} here: {prod_path} \n')
            print(
                f'If you want to remove the {type(self).__name__} capability, just call Naas.input.delete() in this file')
        return self.manager.add_prod({"type": self.role, "path": current_file, "params": {}, "value": 'Only internal'}, silent)

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
        print('.add(path) => add path to the prod server\n')
        print(f'.delete(path) => delete path to the prod {type(self).__name__} server\n')
        print('.clear_history(path, histonumber) => clear history, history number and path are optionel, if you don\'t provide them it will erase full history of current file \n')
        print('.list_history(path) => list history, of a path or if not provided the current file \n')
        print('.get_history(path, histonumber) => get history file, of a path or if not provided the current file \n')
        print('.get(path) => get current prod file of a path, or if not provided the current file \n')
        print(f'.currents() => get current list of {type(self).__name__} prod file\n')
        print(f'.current_raw() => get json current list of {type(self).__name__} prod file\n')
        