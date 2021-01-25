from .types import t_delete, t_job, t_add, t_env, error_busy, error_reject
from IPython.core.display import display, HTML
from .runner.proxy import encode_proxy_url
from .runner.env_var import n_env
import ipywidgets as widgets
import pandas as pd
import traceback
import ipykernel
import requests
import base64
import copy
import uuid
import os


enterprise_gateway = False
try:
    import enterprise_gateway.services.kernels.remotemanager  # noqa: F401

    enterprise_gateway = True  # noqa: F811
except ImportError:
    pass


class Manager:
    __filetype = None
    headers = None

    def __init__(self, filetype):
        self.headers = {"Authorization": f"token {n_env.token}"}
        self.__filetype = filetype
        self.set_runner_mode()

    def is_production(self):
        return False if self.notebook_path() else True

    def set_runner_mode(self):
        try:
            r = requests.get(
                f"{n_env.api}/{t_env}",
            )
            r.raise_for_status()
        except Exception:
            n_env.remote_mode = not n_env.remote_mode

    def get(self):
        public_url = f"{encode_proxy_url()}"
        print("You can check your current tasks list here :")
        display(HTML(f'<a href="{public_url}"">Manager</a>'))

    def get_logs(self):
        req = requests.get(url=f"{n_env.api}/logs")
        req.raise_for_status()
        jsn = req.json()
        return jsn

    def get_naas(self):
        naas_data = []
        try:
            r = requests.get(f"{n_env.api}/{t_job}")
            r.raise_for_status()
            naas_data = r.json()
        except requests.exceptions.ConnectionError:
            print(error_busy)
        except requests.exceptions.HTTPError as e:
            print(error_reject, e)
        return naas_data

    def get_value(self, path):
        try:
            r = requests.get(
                f"{n_env.api}/{t_job}",
                params={
                    "path": path,
                    "type": self.__filetype,
                    "light": True,
                },
            )
            r.raise_for_status()
            data = r.json()
            return data.get("value")
        except requests.exceptions.ConnectionError as err:
            print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            print(error_reject, err)
            raise

    def notebook_path(self):
        try:
            connection_file = os.path.basename(ipykernel.get_connection_file())
            kernel_id = connection_file.split("-", 1)[1].split(".")[0]
            if enterprise_gateway:
                kernel_id = connection_file.split("-", 1)[1].split("_")[0]
            notebooks = self.running_notebooks()
            for notebook in notebooks:
                if kernel_id in notebook["kernel_id"]:
                    return os.path.join(n_env.server_root, notebook["path"])
        except Exception as e:
            tb = traceback.format_exc()
            print("notebook_path", e, tb)
        return None

    def running_notebooks(self):
        try:
            base_url = f"{n_env.hub_api}/user/{n_env.user}/api/sessions"
            req = requests.get(url=base_url, headers=self.headers)
            req.raise_for_status()
            sessions = req.json()
            notebooks = [
                {
                    "kernel_id": notebook["kernel"]["id"],
                    "path": notebook["notebook"]["path"],
                }
                for notebook in sessions
            ]
            return notebooks
        except requests.exceptions.ConnectionError as e:
            print(e)
        except requests.exceptions.HTTPError as e:
            print(e)
        except Exception as e:
            tb = traceback.format_exc()
            print("running_notebooks", e, tb)
        return []

    def get_path(self, path):
        if path is not None:
            return os.path.abspath(os.path.join(os.getcwd(), path))
        else:
            return self.notebook_path()

    def copy_clipboard(self, text):
        uid = uuid.uuid4().hex
        js = """<script>
        function copyToClipboard_{uid}(text) {
            const dummy = document.createElement("textarea");
            document.body.appendChild(dummy);
            dummy.value = text;
            dummy.select();
            document.execCommand("copy");
            document.body.removeChild(dummy);
        }
        </script>"""
        js = js.replace("{uid}", uid)
        display(HTML(js))
        js2 = f"<script>copyToClipboard_{uid}(`" + text + "`);</script>"
        display(HTML(js2))

    def copy_url(self, text):
        button = widgets.Button(description="Copy URL", button_style="primary")
        output = widgets.Output()

        def on_button_clicked(b):
            with output:
                self.copy_clipboard(text)
                html_div = '<div id="pasting_to_clipboard">✅ Copied !</div>'
                display(HTML(html_div))

        button.on_click(on_button_clicked)
        display(button, output)

    def proxy_url(self, endpoint, token=None):
        public_url = encode_proxy_url(endpoint)
        if token:
            public_url = f"{public_url}/{token}"
        return public_url

    def __open_file(self, path):
        filename = os.path.basename(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"file doesn't exist {path}")
        data = open(path, "rb").read()
        encoded = base64.b64encode(data)
        return {"filename": filename, "data": encoded.decode("ascii")}

    def safe_filepath(self, path):
        path = os.path.join(n_env.server_root, path)
        return path

    def __save_file(self, path, filedata=None):
        dirname = os.path.dirname(path)
        filename = filedata["filename"] or os.path.basename(path)
        new_path = os.path.join(dirname, filename)
        if not filedata:
            return
        if os.path.exists(new_path):
            raise FileNotFoundError(f"file already exist {new_path}")
        f = open(new_path, "wb")
        decoded = base64.b64decode(filedata["data"])
        f.write(decoded)
        f.close()

    def clear_file(self, path=None, mode=None, histo=None):
        if not path and self.is_production():
            print("No clear_prod done you are in production\n")
            return
        prod_path = self.get_path(path)
        try:
            r = requests.delete(
                f"{n_env.api}/{t_job}",
                params={"path": prod_path, "histo": histo, "mode": mode},
            )
            r.raise_for_status()
            res = r.json()
            for ff in res:
                print(f"🕣 Your file {ff} has been remove from production.\n")
            return pd.DataFrame(data=res.get("files", []))
        except requests.exceptions.ConnectionError as err:
            print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            print(error_reject, err)
            raise

    def list_prod(self, mode, path=None):
        if not path and self.is_production():
            print("No list_prod done you are in production\n")
            return []
        current_file = self.get_path(path)
        try:
            r = requests.get(
                f"{n_env.api}/{t_job}",
                params={"path": current_file, "type": self.__filetype, "mode": mode},
            )
            r.raise_for_status()
            res = r.json()
            if res.get("files", None) and len(res.get("files", [])) > 0:
                return pd.DataFrame(data=res.get("files", []))
            else:
                print("No files found in prod")
                return []
        except requests.exceptions.ConnectionError as err:
            print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            print(error_reject, err)
            raise

    def get_file(self, path=None, mode=None, histo=None):
        if not path and self.is_production():
            print("No get_prod done you are in production\n")
            return
        current_file = self.get_path(path)
        filename = os.path.basename(current_file)
        try:
            r = requests.get(
                f"{n_env.api}/{t_job}",
                params={
                    "path": current_file,
                    "type": self.__filetype,
                    "mode": mode,
                    "histo": histo,
                },
            )
            r.raise_for_status()
            res = r.json()
            self.__save_file(self.safe_filepath(current_file), res.get("file"))
            print(
                f"🕣 Your Notebook {mode or ''} {filename}, has been copied into your local folder.\n"
            )
        except requests.exceptions.ConnectionError as err:
            print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            print(error_reject, err)
            raise

    def path(self, filetype):
        def mode_path(self, path):
            nonlocal filetype
            if self.is_production():
                # filename = os.path.basename(path)
                # dirname = os.path.dirname(path)
                # filename = f"{filetype}_{filename}"
                # type_path = os.path.join(dirname, filename)
                type_path = path
                return self.get_path(type_path)
            else:
                return path

        return mode_path

    def add_prod(self, obj, debug):
        if "type" in obj and "path" in obj and "params" in obj and "value" in obj:
            new_obj = copy.copy(obj)
            dev_path = obj.get("path")
            new_obj["path"] = self.get_path(dev_path)
            new_obj["file"] = self.__open_file(dev_path)
            new_obj["status"] = t_add
            try:
                if debug:
                    print(f'{new_obj["status"]} ==> {new_obj}')
                r = requests.post(f"{n_env.api}/{t_job}", json=new_obj)
                r.raise_for_status()
                res = r.json()
                if debug:
                    print(f'{res["status"]} ==> {res}')
            except requests.exceptions.ConnectionError as err:
                print(error_busy, err)
                raise
            except requests.exceptions.HTTPError as err:
                print(error_reject, err)
                raise
            return new_obj
        else:
            raise ValueError(
                'obj should have all keys ("type","path","params","value")'
            )

    def del_prod(self, obj, debug):
        if "type" in obj and "path" in obj:
            new_obj = copy.copy(obj)
            new_obj["path"] = self.get_path(obj.get("path"))
            new_obj["params"] = {}
            new_obj["file"] = None
            new_obj["value"] = None
            new_obj["status"] = t_delete
            try:
                if debug:
                    print(f'{new_obj["status"]} ==> {new_obj}')
                r = requests.post(f"{n_env.api}/{t_job}", json=new_obj)
                r.raise_for_status()
                res = r.json()
                if debug:
                    print(f'{res["status"]} ==> {res}')
            except requests.exceptions.ConnectionError as err:
                print(error_busy, err)
                raise
            except requests.exceptions.HTTPError as err:
                print(error_reject, err)
                raise
            return new_obj
        else:
            raise ValueError('obj should have keys ("type","path")')
