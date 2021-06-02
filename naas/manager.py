from .ntypes import (
    t_delete,
    t_performance,
    t_storage,
    t_job,
    t_env,
    t_skip,
    t_send,
    t_error,
    error_busy,
    error_reject,
)
from IPython.core.display import display, HTML
from .runner.proxy import encode_proxy_url
from .runner.env_var import n_env
import pandas as pd
import traceback
import ipykernel
import subprocess
import requests
import base64
import copy
import os


enterprise_gateway = False
try:
    import enterprise_gateway.services.kernels.remotemanager  # noqa: F401

    enterprise_gateway = True  # noqa: F811
except ImportError:
    pass


class Manager:
    __filetype = None
    headers = {"Authorization": f"token {n_env.token}"}

    def __init__(self, filetype=None):
        self.headers = {"Authorization": f"token {n_env.token}"}
        self.__filetype = filetype
        self.set_runner_mode()

    def get_size(self):
        response = requests.get(
            f"{n_env.api}/{t_performance}/{t_storage}", headers=self.headers
        )
        data = response.json()
        if data and data.get(f"{t_storage}"):
            print("📝 Memory used", data.get(f"{t_storage}"))
        else:
            print("😢 Cannot get Memory usage", data.get(t_error))

    def reload_jobs(self):
        response = requests.put(
            f"{n_env.api}/{t_job}", headers=self.headers, params={"reload_jobs": "yes"}
        )
        data = response.json()
        if data and data.get("status") == t_send:
            print("✅ Jobs reloaded from save")
        else:
            print("😢 Jobs cannot be reloaded", data.get(t_error))

    def move_job(self, old_path, new_path):
        if self.is_production():
            print("No move_job done you are in production\n")
            return
        old_path = os.path.abspath(os.path.join(os.getcwd(), old_path))
        new_path = os.path.abspath(os.path.join(os.getcwd(), new_path))
        response = requests.put(
            f"{n_env.api}/{t_job}",
            headers=self.headers,
            params={
                "move": "yes",
                "type": self.__filetype,
                "old_path": old_path,
                "new_path": new_path,
            },
        )
        res = response.json()
        if res and res.get("status") == t_send:
            for ff in res.get("data"):
                print(f"✅ Job {ff.get('from')} moved to {ff.get('to')}\n")
        else:
            print(f"😢 Job cannot be moved to {new_path}", res.get(t_error))

    def is_production(self):
        return True if n_env.current.get("env") == "RUNNER" else False

    def set_runner_mode(self):
        try:
            r = requests.get(f"{n_env.api}/{t_env}", headers=self.headers, timeout=2)
            r.raise_for_status()
        except Exception:
            n_env.remote_mode = not n_env.remote_mode

    def get(self):
        public_url = f"{encode_proxy_url()}"
        print("You can check your current tasks list here :")
        display(HTML(f'<a href="{public_url}"">Manager</a>'))

    def get_logs(self):
        req = requests.get(url=f"{n_env.api}/logs", headers=self.headers)
        req.raise_for_status()
        jsn = req.json()
        return jsn

    def get_naas(self):
        naas_data = []
        try:
            r = requests.get(f"{n_env.api}/{t_job}", headers=self.headers)
            r.raise_for_status()
            naas_data = r.json()
        except requests.exceptions.ConnectionError:
            print(error_busy)
        except requests.exceptions.HTTPError as e:
            print(error_reject, e)
        return naas_data

    def get_value(self, path, do_print=True):
        try:
            r = requests.get(
                f"{n_env.api}/{t_job}",
                params={
                    "path": path,
                    "type": self.__filetype,
                    "light": True,
                },
                headers=self.headers,
            )
            r.raise_for_status()
            data = r.json()
            return data.get("value")
        except requests.exceptions.ConnectionError as err:
            if do_print:
                print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            if do_print:
                print(error_reject, err)
            raise

    def notebook_path(self):
        if self.is_production():
            return os.path.join(n_env.server_root, n_env.current.get("path"))
        try:
            notebooks = self.running_notebooks()
            try:
                connection_file = os.path.basename(ipykernel.get_connection_file())
                kernel_id = connection_file.split("-", 1)[1].split(".")[0]
                if enterprise_gateway:
                    kernel_id = connection_file.split("-", 1)[1].split("_")[0]
                for notebook in notebooks:
                    if kernel_id in notebook["kernel_id"]:
                        return os.path.join(n_env.server_root, notebook["path"])
            except Exception:
                process_id = os.getpid()
                for notebook in notebooks:
                    if process_id in notebook["process_ids"]:
                        return os.path.join(n_env.server_root, notebook["path"])
        except Exception as e:
            tb = traceback.format_exc()
            print("notebook_path", e, tb)
        return None

    def __get_process_ids(self, name):
        try:
            child = subprocess.Popen(
                ["pgrep", "-f", name], stdout=subprocess.PIPE, shell=False
            )
            response = child.communicate()[0]
            return [int(pid) for pid in response.split()]
        except Exception:
            return []

    def running_notebooks(self):
        try:
            base_url = f"{n_env.user_url}/api/sessions"
            req = requests.get(url=base_url, headers=self.headers)
            req.raise_for_status()
            sessions = req.json()
            sessions = filter(lambda item: "notebook" in item["type"], sessions)
            notebooks = [
                {
                    "kernel_id": notebook["kernel"]["id"],
                    "path": notebook["notebook"]["path"],
                    "process_ids": self.__get_process_ids(notebook["kernel"]["id"]),
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
            base_path = os.getcwd()
            if self.is_production():
                base_path = base_path.replace(n_env.path_naas_folder, "")
            return os.path.abspath(os.path.join(base_path, path))
        else:
            return self.notebook_path()

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
        return new_path

    def clear_file(self, path=None, mode=None, histo=None):
        if not path and self.is_production():
            print("No clear_prod done you are in production\n")
            return
        prod_path = self.get_path(path)
        try:
            r = requests.delete(
                f"{n_env.api}/{t_job}",
                headers=self.headers,
                params={
                    "path": prod_path,
                    "type": self.__filetype,
                    "histo": histo,
                    "mode": mode,
                },
            )
            r.raise_for_status()
            res = r.json()
            if res.get("status") == t_error or res.get("status") == t_skip:
                raise ValueError(f"❌ Cannot clean your file {path}")
            for ff in res.get("data"):
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
                headers=self.headers,
                params={"path": current_file, "type": self.__filetype, "mode": mode},
            )
            r.raise_for_status()
            res = r.json()
            if res.get("status") == t_error or res.get("status") == t_skip:
                raise ValueError(f"❌ Cannot list your file {path}")
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
        if self.is_production():
            print("No get_prod done you are in production\n")
            return
        current_file = self.get_path(path)
        filename = os.path.basename(current_file)
        try:
            r = requests.get(
                f"{n_env.api}/{t_job}",
                headers=self.headers,
                params={
                    "path": current_file,
                    "type": self.__filetype,
                    "mode": mode,
                    "histo": histo,
                },
            )
            r.raise_for_status()
            res = r.json()
            if res.get("status") == t_error or res.get("status") == t_skip:
                raise ValueError(f"❌ Cannot get your file {path}")
            new_path = self.__save_file(
                self.safe_filepath(current_file), res.get("file")
            )
            print(
                f"🕣 Your Notebook {mode or ''} {filename}, has been copied into your local folder.\n"
            )
            return new_path
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
            # new_obj["status"] = t_add
            try:
                if debug:
                    print(f'{new_obj["status"]} ==> {new_obj}')
                r = requests.post(
                    f"{n_env.api}/{t_job}", json=new_obj, headers=self.headers
                )
                r.raise_for_status()
                res = r.json()
                if res.get("status") == t_error or res.get("status") == t_skip:
                    raise ValueError(f"❌ Cannot add your file {obj.get('path')}")
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
                r = requests.post(
                    f"{n_env.api}/{t_job}", json=new_obj, headers=self.headers
                )
                r.raise_for_status()
                res = r.json()
                if res.get("status") == t_error or res.get("status") == t_skip:
                    raise ValueError(f"❌ Cannot delete your file {obj.get('path')}")
                if debug:
                    print(f'{res.get("status")} ==> {res}')
            except requests.exceptions.ConnectionError as err:
                print(error_busy, err)
                raise
            except requests.exceptions.HTTPError as err:
                print(error_reject, err)
                raise
            return new_obj
        else:
            raise ValueError('obj should have keys ("type","path")')
