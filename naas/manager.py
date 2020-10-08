from .types import t_delete, t_job, t_add
from notebook import notebookapp
from .runner.proxy import encode_proxy_url
from shutil import copy2
import ipykernel
import requests
import datetime
import urllib
import errno
import json
import os
from IPython.core.display import display, HTML
import ipywidgets as widgets
import copy


class Manager:
    __local_api = f'http://localhost:{os.environ.get("NAAS_RUNNER_PORT", 5000)}'
    __error_manager_busy = "Manager look busy, try to reload your machine"
    __error_manager_reject = "Manager refused your request, reason :"
    __base_ftp_path = None
    __public_url = None
    __jup_user = None
    __jup_token = None
    __production_path = None
    __folder_name = ".naas"
    __readme_name = "README.md"
    __readme_path = None

    def __init__(self):
        self.__base_ftp_path = os.environ.get(
            "JUPYTER_SERVER_ROOT", f'/home/{os.environ.get("NB_USER", "ftp")}'
        )
        self.__public_url = os.environ.get("JUPYTERHUB_URL", "")
        self.__jup_token = os.environ.get("JUPYTERHUB_API_TOKEN", "")
        self.__jup_user = os.environ.get("JUPYTERHUB_USER", "")
        self.__production_path = os.path.join(self.__base_ftp_path, self.__folder_name)
        self.__readme_path = os.path.join(self.__production_path, self.__readme_name)
        if not os.path.exists(self.__production_path):
            try:
                os.makedirs(self.__production_path)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        try:
            with open(self.__readme_path, "w+") as readme:
                readme.write("Welcome NAAS")
                readme.close()
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    def get_naas(self):
        naas_data = []
        try:
            r = requests.get(f"{self.__local_api}/{t_job}")
            naas_data = r.json()
        except ConnectionError:
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
        """Returns the absolute path of the Notebook or None if it cannot be determined
        NOTE: works only when the security is token-based or there is also no password
        """
        try:
            connection_file = os.path.basename(ipykernel.get_connection_file())
            kernel_id = connection_file.split("-", 1)[1].split(".")[0]
            for srv in notebookapp.list_running_servers():
                try:
                    base_url = (
                        f"{self.__public_url}/user/{self.__jup_user}/api/sessions"
                    )
                    req = urllib.request.urlopen(f"{base_url}?token={self.__jup_token}")
                    sessions = json.load(req)
                    for sess in sessions:
                        if sess["kernel"]["id"] == kernel_id:
                            return os.path.join(
                                srv["notebook_dir"], sess["notebook"]["path"]
                            )
                except urllib.error.HTTPError:
                    pass
        except IndexError:
            pass
        except RuntimeError:
            pass
        return None

    def get_path(self, path):
        if path is not None:
            return os.path.abspath(os.path.join(os.getcwd(), path))
        else:
            return self.notebook_path()

    def copy_clipboard(self, text):
        js = """<script>
        function copyToClipboard(text) {
        var dummy = document.createElement("textarea");
        document.body.appendChild(dummy);
        dummy.value = text;
        dummy.select();
        document.execCommand("copy");
        document.body.removeChild(dummy);
        }
        </script>"""
        display(HTML(js))
        js2 = "<script>copyToClipboard(`" + text + "`);</script>"
        display(HTML(js2))

    def copy_url(self, text):
        button = widgets.Button(description="Copy URL")
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
        new_path = path.replace(self.__base_ftp_path, self.__production_path)
        return new_path

    def __copy_file_in_dev(self, path):
        new_path = self.get_prod_path(path)
        if not os.path.exists(new_path):
            raise FileNotFoundError(f"file doesn't exist {new_path}")
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        dev_dir = os.path.dirname(path)
        dev_finename = os.path.basename(path)
        secure_path = os.path.join(dev_dir, f"prod_{dev_finename}")
        try:
            copy2(new_path, secure_path)
        except Exception as e:
            raise FileExistsError(
                f"Cannot copied here {secure_path}, file probabily exist {path} {str(e)}"
            )
        print(f"File copied here {secure_path}")
        return secure_path

    def __copy_file_in_prod(self, path):
        new_path = self.get_prod_path(path)
        prod_dir = os.path.dirname(new_path)
        prod_finename = os.path.basename(new_path)
        history_filename = (
            f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}_{prod_finename}'
        )
        history_path = os.path.join(prod_dir, history_filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"file doesn't exist {path}")
        if not os.path.exists(os.path.dirname(new_path)):
            try:
                os.makedirs(os.path.dirname(new_path))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        if os.path.exists(new_path):
            os.remove(new_path)
        copy2(path, new_path)
        copy2(path, history_path)
        return new_path

    def __del_file_in_prod(self, path):
        if path.find(self.__production_path) == -1:
            raise FileNotFoundError(
                f"Cannot delte file {path} it's in other folder than {self.__production_path}"
            )
        if os.path.exists(path):
            os.remove(path)
        else:
            raise FileNotFoundError(f"File {path} not Found")

    def get_out_path(self, path):
        current_path = self.get_path(path)
        filename = os.path.basename(current_path)
        dirname = os.path.dirname(current_path)
        out_path = os.path.join(dirname, f"out_{filename}")
        return out_path

    def get_output(self, path=None):
        out_path = self.get_out_path(path)
        self.__copy_file_in_dev(out_path)
        print(
            "🕣 Your Notebook OUTPUT from production folder has been copied into your dev folder\n"
        )

    def clear_output(self, path=None):
        out_path = self.get_out_path(path)
        if os.path.exists(out_path):
            os.remove(out_path)
            print("🕣 Your Notebook output has been remove from production folder.\n")
        else:
            raise FileNotFoundError(f"File {out_path} not Found")

    def get_prod(self, path=None, histo=None):
        current_file = self.get_path(path)
        if histo:
            filename = os.path.basename(current_file)
            dirname = os.path.dirname(current_file)
            path_histo = os.path.join(dirname, f"{histo}_{filename}")
            self.__copy_file_in_dev(path_histo)
        else:
            self.__copy_file_in_dev(current_file)
        print(
            "🕣 Your Notebook from production folder has been copied into your dev folder.\n"
        )

    def list_prod(self, path=None):
        current_file = self.get_path(path)
        prod_path = self.get_prod_path(current_file)
        filename = os.path.basename(current_file)
        dirname = os.path.dirname(prod_path)
        print("Avaliable :\n")
        for ffile in os.listdir(dirname):
            if (
                ffile.endswith(filename)
                and ffile != filename
                and not ffile.startswith("out")
            ):
                histo = ffile.replace(filename, "")
                histo = histo.replace("_", "")
                print(histo + "\n")

    def clear_prod(self, path=None, histo=None):
        current_file = self.get_path(path)
        prod_path = self.get_prod_path(current_file)
        filename = (
            os.path.basename(current_file)
            if not histo
            else f"{histo}_{os.path.basename(current_file)}"
        )
        dirname = os.path.dirname(prod_path)
        for ffile in os.listdir(dirname):
            if not ffile.startswith("out_") and (
                (histo and filename == ffile)
                or (not histo and ffile.endswith(filename) and filename != ffile)
            ):
                tmp_path = os.path.join(dirname, ffile)
                print(f"Delete {tmp_path}")
                os.remove(tmp_path)

    def add_prod(self, obj, debug):
        if "type" in obj and "path" in obj and "params" in obj and "value" in obj:
            new_obj = copy.copy(obj)
            dev_path = obj.get("path")
            self.__copy_file_in_prod(dev_path)
            new_obj["path"] = self.get_prod_path(dev_path)
            new_obj["status"] = t_add
            try:
                if debug:
                    print(f'{new_obj["status"]} ==> {new_obj}')
                r = requests.post(f"{self.__local_api}/{t_job}", json=new_obj)
                r.raise_for_status()
                res = r.json()
                if debug:
                    print(f'{res["status"]} ==> {res}')
            except ConnectionError as err:
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
            self.__del_file_in_prod(new_obj["path"])
            try:
                if debug:
                    print(f'{new_obj["status"]} ==> {new_obj}')
                r = requests.post(f"{self.__local_api}/{t_job}", json=new_obj)
                r.raise_for_status()
                res = r.json()
                if debug:
                    print(f'{res["status"]} ==> {res}')
            except ConnectionError as err:
                print(self.__error_manager_busy, err)
                raise
            except requests.HTTPError as err:
                print(self.__error_manager_reject, err)
                raise
            return new_obj
        else:
            raise ValueError('obj should have keys ("type","path")')
