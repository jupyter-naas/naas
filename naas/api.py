from IPython.core.display import display, HTML, JSON, Image, SVG, Markdown
from .types import t_notebook
from .manager import Manager
import pandas as pd
import os


class Api:
    naas = None
    role = t_notebook

    def __init__(self):
        self.manager = Manager()

    def current_raw(self):
        json_data = self.manager.get_naas()
        for item in json_data:
            if item["type"] == self.role:
                print(item)

    def currents(self):
        json_data = self.manager.get_naas()
        for item in json_data:
            kind = None
            if item["type"] == self.role:
                kind = f"callable with this url {self.manager.proxy_url('notebooks', item['value'])} from anywhere"
                print(f"File ==> {item['path']} is {kind}")

    def add(self, path=None, params={}, debug=False):
        current_file = self.manager.get_path(path)
        if current_file is None:
            print("Missing file path in prod mode")
            return
        prod_path = self.manager.get_prod_path(current_file)
        token = self.manager.get_value(prod_path, self.role)
        if token is None:
            token = os.urandom(30).hex()
        url = self.manager.proxy_url(self.role, token)
        if not self.manager.notebook_path():
            print("No add done you are in already in naas folder\n")
            return url
        print("👌 Well done! Your Notebook has been sent to production folder.\n")
        print(f"🔑 You can run this notebook remotely with: {url} \n")
        self.manager.copy_url(url)
        print(
            'PS: to remove the "Notebook as API" feature, just replace .add by .delete'
        )
        self.manager.add_prod(
            {"type": self.role, "path": current_file, "params": params, "value": token},
            not debug,
        )
        return url

    def respond_html(self, data):
        display(HTML(data, metadata={"naas_api": True}))

    def respond_json(self, data):
        display(JSON(data, metadata={"naas_api": True}))

    def respond_image(self, data, filename, mimetype):
        display(
            Image(data, filename=filename, format=mimetype, metadata={"naas_api": True})
        )

    def respond_svg(self, data):
        display(SVG(data, metadata={"naas_api": True}))

    def respond_markdown(self, data):
        display(Markdown(data, metadata={"naas_api": True}))

    def respond_csv(self, data):
        if not isinstance(data, pd.DataFrame):
            raise Exception("data shoud be a dataframe")
        display(HTML(data.to_html(), metadata={"naas_api": True, "naas_type": "csv"}))

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

    def delete(self, path=None, all=False, debug=False):
        if not self.manager.notebook_path():
            print("No delete done you are in already in naas folder\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, not debug)
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
            ".clear_history(path, histonumber) => clear history, history number and path are optionel, \
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
            f".current_raw() => get json current list of {type(self).__name__} prod file\n"
        )
