from IPython.core.display import display, HTML, JSON, Image, SVG, Markdown
from .types import t_notebook, t_output, guess_type
from .manager import Manager
import pandas as pd
import markdown2
import warnings
import os


class Api:
    naas = None
    role = t_notebook
    manager = None
    deprecated_name = False

    def __init__(self, deprecated_name=False):
        self.deprecated_name = deprecated_name
        self.manager = Manager(t_notebook)
        self.path = self.manager.path

    def deprecatedPrint(self):
        # TODO remove this in june 2021
        if self.deprecated_name:
            warnings.warn(
                "[Warning], naas.api is deprecated,\n use naas.webhook instead it will be remove in 1 june 2021"
            )

    def list(self, path=None):
        self.deprecatedPrint()
        return self.manager.list_prod("list_history", path)

    def list_output(self, path=None):
        self.deprecatedPrint()
        return self.manager.list_prod("list_output", path)

    def get(self, path=None, histo=None):
        self.deprecatedPrint()
        return self.manager.get_file(path, histo=histo)

    def get_output(self, path=None, histo=None):
        self.deprecatedPrint()
        return self.manager.get_file(path, t_output, histo)

    def clear(self, path=None, histo=None):
        self.deprecatedPrint()
        return self.manager.clear_file(path, None, histo)

    def clear_output(self, path=None, histo=None):
        self.deprecatedPrint()
        return self.manager.clear_file(path, t_output, histo)

    def currents(self, raw=False):
        self.deprecatedPrint()
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

    def add(self, path=None, params={}, debug=False, force=False):
        self.deprecatedPrint()
        current_file = self.manager.get_path(path)
        if current_file is None:
            print("Missing file path in prod mode")
            return
        token = os.urandom(30).hex()
        if not force:
            try:
                token = self.manager.get_value(current_file)
            except:  # noqa: E722
                pass
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
        self.deprecatedPrint()
        display(
            Markdown(
                "Response Set as Notebook !",
                metadata={"naas_api": True, "naas_type": t_notebook},
            )
        )

    def respond_file(self, path):
        self.deprecatedPrint()
        abs_path = os.path.abspath(path)
        naas_type = guess_type(abs_path)
        display(Markdown("Response Set as File, preview below: "))
        display(
            JSON(
                {"path": abs_path}, metadata={"naas_api": True, "naas_type": naas_type}
            )
        )

    def respond_html(self, data):
        self.deprecatedPrint()
        display(Markdown("Response Set as HTML, preview below: "))
        display(HTML(data, metadata={"naas_api": True}))

    def respond_json(self, data):
        self.deprecatedPrint()
        display(Markdown("Response Set as JSON, preview below: "))
        display(JSON(data, metadata={"naas_api": True}))

    def respond_image(self, data=None, filename=None):
        self.deprecatedPrint()
        display(Markdown("Response Set as IMAGE, preview below: "))
        display(Image(data, filename=filename, metadata={"naas_api": True}))

    def respond_svg(self, data):
        self.deprecatedPrint()
        display(Markdown("Response Set as SVG, preview below: "))
        display(SVG(data, metadata={"naas_api": True}))

    def respond_text(self, data):
        self.deprecatedPrint()
        display(Markdown("Response Set as Text, preview below: "))
        display(HTML(data, metadata={"naas_api": True, "naas_type": "text"}))

    def respond_markdown(self, data):
        self.deprecatedPrint()
        display(Markdown("Response Set as Markdown, preview below: "))
        html = markdown2.markdown(data)
        display(HTML(html, metadata={"naas_api": True, "naas_type": "markdown"}))

    def respond_csv(self, data):
        self.deprecatedPrint()
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data shoud be a dataframe")
        display(HTML(data.to_html(), metadata={"naas_api": True, "naas_type": "csv"}))

    def delete(self, path=None, all=False, debug=False):
        self.deprecatedPrint()
        if self.manager.is_production():
            print("No delete done you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Notebook has been remove from production.\n")
        if all is True:
            self.clear(path)
            self.clear_output(path)
