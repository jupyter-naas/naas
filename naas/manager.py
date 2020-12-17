from IPython.core.display import display, HTML
from .runner.proxy import encode_proxy_url
from .types import t_delete, t_job, t_add
from .runner.env_var import n_env
import ipywidgets as widgets
import pandas as pd
import ipykernel
import requests
import errno
import copy
import uuid
import os
import traceback
import base64


enterprise_gateway = False
try:
    import enterprise_gateway.services.kernels.remotemanager  # noqa: F401

    enterprise_gateway = True  # noqa: F811
except ImportError:
    pass


class Manager:
    __error_manager_busy = "Manager look busy, try to reload your machine"
    __error_manager_reject = "Manager refused your request, reason :"
    __production_path = None
    __folder_name = ".naas"
    __filetype = None
    headers = None

    def __init__(self, filetype):
        self.headers = {"Authorization": f"token {n_env.token}"}
        self.__filetype = filetype
        self.__production_path = os.path.join(n_env.server_root, self.__folder_name)
        if not os.path.exists(self.__production_path):
            try:
                os.makedirs(self.__production_path)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise

    def is_production(self):
        return False if self.notebook_path() else True

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
            print(self.__error_manager_busy)
        except requests.HTTPError as e:
            print(self.__error_manager_reject, e)
        return naas_data

    def get_value(self, path, obj_type):
        json_data = self.get_naas()
        value = None
        for item in json_data:
            if item["type"] == obj_type and item["path"] == path:
                value = item["value"]
        return value

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
        except requests.HTTPError as e:
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

    def get_prod_path(self, path):
        return path.replace(n_env.server_root, self.__production_path)

    def __open_file(self, path):
        filename = os.path.basename(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"file doesn't exist {path}")
        data = open(path, "rb").read()
        encoded = base64.b64encode(data)
        return {"filename": filename, "data": encoded.decode("ascii")}

    def __save_file(self, path, data=None):
        if not data:
            return
        if not os.path.exists(path):
            raise FileNotFoundError(f"file doesn't exist {path}")
        f = open(path, "wb")
        decoded = base64.b64decode(data)
        f.write(decoded)
        f.close()

    def clear_file(self, path=None, mode=None, histo=None):
        if not path and self.is_production():
            print("No clear_prod done you are in production\n")
            return
        current_file = self.get_path(path)
        prod_path = self.get_prod_path(current_file)
        try:
            r = requests.delete(
                f"{n_env.api}/{t_job}",
                json={"path": prod_path, "histo": histo, "mode": mode},
            )
            r.raise_for_status()
            res = r.json()
            for ff in res:
                print(f"🕣 Your Notebook output {ff} has been remove from production.\n")
            return pd.DataFrame(data=res.get("files", []))
        except requests.exceptions.ConnectionError as err:
            print(self.__error_manager_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_manager_reject, err)
            raise

    def list_prod(self, mode, path=None):
        if not path and self.is_production():
            print("No list_prod done you are in production\n")
            return
        current_file = self.get_path(path)
        prod_path = self.get_prod_path(current_file)
        try:
            r = requests.get(
                f"{n_env.api}/{t_job}",
                json={"path": prod_path, "type": self.__filetype, "mode": mode},
            )
            r.raise_for_status()
            res = r.json()
            if res.get("files", None):
                return pd.DataFrame(data=res.get("files", []))
            else:
                return pd.DataFrame(data=res)
        except requests.exceptions.ConnectionError as err:
            print(self.__error_manager_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_manager_reject, err)
            raise

    def get_file(self, path=None, mode=None):
        if not path and self.is_production():
            print("No get_prod done you are in production\n")
            return
        current_file = self.get_path(path)
        filename = os.path.basename(current_file)
        if mode:
            dirname = os.path.dirname(current_file)
            filename = f"{mode}_{filename}"
            current_file = os.path.join(dirname, filename)
        prod_path = self.get_prod_path(current_file)
        try:
            r = requests.get(
                f"{n_env.api}/{t_job}",
                json={"path": prod_path, "type": self.__filetype, "mode": mode},
            )
            r.raise_for_status()
            res = r.json()
            self.__save_file(current_file, res.get("file"))
            print(
                f"🕣 Your Notebook {filename} from {mode} has been copied into your local folder.\n"
            )
            return res
        except requests.exceptions.ConnectionError as err:
            print(self.__error_manager_busy, err)
            raise
        except requests.HTTPError as err:
            print(self.__error_manager_reject, err)
            raise

    def path(self, path):
        if self.manager.is_production():
            return self.get_prod_path(path)
        else:
            return path

    def add_prod(self, obj, debug):
        if "type" in obj and "path" in obj and "params" in obj and "value" in obj:
            new_obj = copy.copy(obj)
            dev_path = obj.get("path")
            new_obj["path"] = self.get_prod_path(dev_path)
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
                print(self.__error_manager_busy, err)
                raise
            except requests.HTTPError as err:
                print(self.__error_manager_reject, err)
                raise
            return new_obj
        else:
            raise ValueError(
                'obj should have all keys ("type","path","params","value")'
            )

    def del_prod(self, obj, debug):
        if "type" in obj and "path" in obj:
            new_obj = copy.copy(obj)
            new_obj["path"] = self.get_prod_path(obj.get("path"))
            new_obj["params"] = {}
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
                print(self.__error_manager_busy, err)
                raise
            except requests.HTTPError as err:
                print(self.__error_manager_reject, err)
                raise
            return new_obj
        else:
            raise ValueError('obj should have keys ("type","path")')
