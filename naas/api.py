from IPython.core.display import display, HTML, JSON, Image, SVG, Markdown
from .types import t_notebook
from .manager import Manager
import pandas as pd
import mimetypes
import os


class Api:
    naas = None
    role = t_notebook

    def __init__(self):
        self.manager = Manager()
        self.get = self.manager.get_prod
        self.list = self.manager.list_prod
        self.clear = self.manager.clear_prod
        self.get_output = self.manager.get_output
        self.clear_output = self.manager.clear_output

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
                    kind = f"callable with this url {self.manager.proxy_url('notebooks', item['value'])}"
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
        if self.manager.is_production():
            print("No add done you are in production\n")
            return url
        self.manager.add_prod(
            {"type": self.role, "path": current_file, "params": params, "value": token},
            debug,
        )
        print("👌 Well done! Your Notebook has been sent to production.\n")
        self.manager.copy_url(url)
        print(
            'PS: to remove the "Notebook as API" feature, just replace .add by .delete'
        )
        return url

    def respond_notebook(self):
        display(
            Markdown(
                "Response Set as Notebook !",
                metadata={"naas_api": True, "naas_type": t_notebook},
            )
        )

    def respond_file(self, path):
        abs_path = os.path.abspath(path)
        naas_type = mimetypes.guess_type(abs_path)[0]
        display(Markdown("Response Set as File, preview below: "))
        display(
            JSON(
                {"path": abs_path}, metadata={"naas_api": True, "naas_type": naas_type}
            )
        )

    def respond_html(self, data):
        display(Markdown("Response Set as HTML, preview below: "))
        display(HTML(data, metadata={"naas_api": True}))

    def respond_json(self, data):
        display(Markdown("Response Set as JSON, preview below: "))
        display(JSON(data, metadata={"naas_api": True}))

    def respond_image(self, data, filename):
        display(Markdown("Response Set as IMAGE, preview below: "))
        display(Image(data, filename=filename, metadata={"naas_api": True}))

    def respond_svg(self, data):
        display(Markdown("Response Set as SVG, preview below: "))
        display(SVG(data, metadata={"naas_api": True}))

    def respond_markdown(self, data):
        display(Markdown("Response Set as Markdown, preview below: "))
        display(Markdown(data, metadata={"naas_api": True}))

    def respond_csv(self, data):
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data shoud be a dataframe")
        display(HTML(data.to_html(), metadata={"naas_api": True, "naas_type": "csv"}))

    def delete(self, path=None, all=False, debug=False):
        if self.manager.is_production():
            print("No delete done you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Notebook has been remove from production.\n")
        if all is True:
            self.clear(path)
            self.clear_output(path)
