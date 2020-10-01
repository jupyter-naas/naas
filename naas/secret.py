import base64
import errno
import json
import os


class Secret:
    __path_user_files = None
    __naas_folder = ".naas"
    __json_name = "secrets.json"

    def __init__(self, clean=False):
        self.__path_user_files = os.environ.get(
            "JUPYTER_SERVER_ROOT", f'/home/{os.environ.get("NB_USER", "ftp")}'
        )
        self.__path_naas_files = os.path.join(
            self.__path_user_files, self.__naas_folder
        )
        self.__json_secrets_path = os.path.join(
            self.__path_naas_files, self.__json_name
        )
        if not os.path.exists(self.__path_naas_files):
            try:
                os.makedirs(self.__path_naas_files)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        if clean:
            print("Init Secret Storage")
            self.__set_secret([])

    def __set_secret(self, new_secret):
        secret_data = json.dumps(new_secret, sort_keys=True, indent=4)
        with open(self.__json_secrets_path, "w+") as f:
            f.write(secret_data)
            f.close()

    def __get_all(self):
        secret_data = []
        try:
            with open(self.__json_secrets_path, "r") as f:
                secret_data = json.load(f)
                f.close()
        except IOError:
            secret_data = []
        return secret_data

    def list(self):
        all_secret = self.__get_all()
        all_keys = []
        for item in all_secret:
            all_keys.append(item["name"])
        return all_keys

    def add(self, name=None, secret=None):
        new_obj = []
        obj = {}
        json_data = self.__get_all()
        replaced = False
        message_bytes = secret.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        secret_base64 = base64_bytes.decode("ascii")
        for item in json_data:
            if name == item["name"]:
                obj = {"name": name, "secret": secret_base64}
                new_obj.append(obj)
                print("Edited =>>", obj)
                replaced = True
            else:
                new_obj.append(item)
        if replaced is False:
            obj = {"name": name, "secret": secret_base64}
            new_obj.append(obj)
            print("Added =>>", obj)
        self.__set_secret(new_obj)
        return None

    def get(self, name=None, default_value=None):
        all_secret = self.__get_all()
        secret_item = None
        for item in all_secret:
            if name == item["name"]:
                secret_item = item
                break
        if secret_item is not None:
            secret_base64 = secret_item.get("secret", None)
            if secret_base64 is not None:
                secret = base64.b64decode(secret_base64)
                return secret.decode("ascii")
        return default_value

    def delete(self, name=None):
        new_obj = []
        found = False
        json_data = self.__get_all()
        for item in json_data:
            if name != item["name"]:
                new_obj.append(item)
            else:
                found = True
        if len(json_data) != len(new_obj):
            self.__set_secret(new_obj)
        if found:
            print("Deleted =>>", name)
        else:
            print("Not found =>>", name)
        return None
