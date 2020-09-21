from IPython.core.display import display, HTML, JSON, Image, SVG, Markdown
from .types import t_notebook
from .manager import Manager
import os

class Api():
    naas = None
    role = t_notebook

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
                kind = f"callable with this url {self.manager.proxy_url('notebooks', item['value'])} from anywhere"
                print(f"File ==> {item['path']} is {kind}")

    def add(self, path=None, params={}, silent=False):
        current_file = self.manager.get_path(path)
        if current_file is None:
            print('Missing file path in prod mode')
            return
        prod_path = self.manager.get_prod_path(current_file)
        token = self.manager.get_value(prod_path, self.role)
        if token is None:
            token = os.urandom(30).hex()
        url = self.manager.proxy_url('notebooks',token)
        if not self.manager.notebook_path():
            print(
                f'No add done you are in already in naas folder\n')
            return url
        if silent is False:
            print(
                f'[Naas from Jupyter] => i have copied this {current_file} here: {prod_path} \n')
            print(
                f'You can now use it in Naas workspace with this url : {url} \n')
            display(HTML(f'<a href="{url}"">{url}</a>'))
            print(
                f'If you want to remove the api capability, just call .delete({path if path is not None else "" })) in this file')
        self.manager.add_prod({"type": self.role, "path": current_file, "params": params, "value": token}, silent)
        return url

    def respond_html(self, data):
        display(HTML(data, metadata={'naas_api': True}))

    def respond_json(self, data):        
        display(JSON(data, metadata={'naas_api': True}))

    def respond_image(self, data, filename, mimetype):
        display(Image(data, filename=filename, format=mimetype, metadata={'naas_api': True}))
        
    def respond_svg(self, data):
        display(SVG(data, metadata={'naas_api': True}))
        
    def respond_markdown(self, data):
        display(Markdown(data, metadata={'naas_api': True}))

    def respond_csv(self, data):
        display(HTML(empDfObj.to_html(), metadata={'naas_api': True, 'naas_type': 'csv'}))

    def get(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.get_prod(current_file)

    def get_output(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.get_output(current_file)

    def clear_output(self, path=None):
        current_file = self.manager.get_path(path)
        self.manager.clear_output(current_file)
                
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
        
    def clear_history(self,  path=None, histo=None):
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
        print('.clear_history(path, histonumber) => clear history, history number and path are optionel, if you don\'t provide them it will erase full history of current file \n')
        print('.list_history(path) => list history, of a path or if not provided the current file \n')
        print('.get_history(histonumber, path) => get history file, of a path or if not provided the current file \n')
        print('.get(path) => get current prod file of a path, or if not provided the current file \n')
        print(f'.currents() => get current list of {type(self).__name__} prod file\n')
        print(f'.current_raw() => get json current list of {type(self).__name__} prod file\n')
