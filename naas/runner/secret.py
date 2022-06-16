from asyncio import Semaphore
from naas.ntypes import (
    t_delete,
    t_add,
    t_skip,
    t_update,
    t_error,
    t_secret,
    t_notebook,
    t_asset,
    t_dependency,
    t_scheduler,
)
import pandas as pd
import datetime
import errno
import json
import os
import uuid
from sanic.exceptions import ServerError
from .env_var import n_env
import base64
import pytz

filters = [t_notebook, t_asset, t_dependency, t_scheduler]
filters_api = [t_notebook, t_asset]


class Secret:
    __storage_sem = None
    __df = None
    __logger = None
    __json_name = "secrets.json"

    def __init__(self, logger, clean=False, init_data=[]):
        self.__json_secrets_path = os.path.join(
            n_env.path_naas_folder, self.__json_name
        )
        self.__storage_sem = Semaphore(1)
        self.__logger = logger
        if not os.path.exists(n_env.path_naas_folder):
            try:
                print("Init Naas folder Secret")
                os.makedirs(n_env.path_naas_folder)
            except OSError as exc:  # Guard against race condition
                print("__path_naas_files", n_env.path_naas_folder)
                if exc.errno != errno.EEXIST:
                    raise
            except Exception as e:
                print("Exception", e)
        if not os.path.exists(self.__json_secrets_path) or clean:
            uid = str(uuid.uuid4())
            try:
                print("Init Secret Storage", self.__json_secrets_path)
                self.__save_to_file(uid, init_data)
                self.__df = None
            except Exception as e:
                print("Exception", e)
                self.__logger.error(
                    {
                        "id": uid,
                        "type": "init_secret_storage",
                        "filepath": self.__json_secrets_path,
                        "status": t_error,
                        "error": str(e),
                    }
                )
        else:
            uid = str(uuid.uuid4())
            self.__load_secrets(uid)
        self.__ensure_df_columns()

    def __load_secrets(self, uid):
        self.__df = self.__get_save_from_file(uid)
        self.__cleanup_secrets()
        self.__ensure_df_columns()

    def __ensure_df_columns(self):
        if self.__df is None or len(self.__df) == 0:
            self.__df = pd.DataFrame(
                columns=[
                    "id",
                    "name",
                    "secret",
                    "lastUpdate",
                ]
            )

    def __cleanup_secrets(self):
        if len(self.__df) > 0:
            self.__dedup_secrets()

    def __dedup_secrets(self):
        new_df = self.__df.drop_duplicates(subset=["name"]).to_dict("records")
        self.__df = pd.DataFrame([*new_df])
        self.__df = self.__df.reset_index(drop=True)

    def __get_save_from_file(self, uid):
        data = []
        try:
            with open(self.__json_secrets_path, "r") as f:
                data = json.load(f)
                f.close()
        except Exception as err:
            self.__logger.error(
                {
                    "id": str(uid),
                    "type": "__get_save_from_file",
                    "status": t_error,
                    "filepath": self.__json_secrets_path,
                    "error": str(err),
                }
            )
        return pd.DataFrame(data).reset_index(drop=True)

    def __save_to_file(self, uid, data):
        try:
            with open(self.__json_secrets_path, "w+") as f:
                f.write(
                    json.dumps(data, sort_keys=True, indent=4).replace("NaN", "null")
                )
                f.close()
        except Exception as err:
            print(f"==> Cannot save {uid} \n\n", err)
            self.__logger.error(
                {
                    "id": str(uid),
                    "type": "__save_to_file",
                    "status": t_error,
                    "filepath": self.__json_secrets_path,
                    "error": str(err),
                }
            )

    async def find_by_name(self, uid, name):
        res = None
        async with self.__storage_sem:
            self.__load_secrets(uid)
            try:
                if len(self.__df) > 0:
                    cur_jobs = self.__df[self.__df.name == name]
                    cur_job = cur_jobs.to_dict("records")
                    if len(cur_job) > 0:
                        res = cur_job[0]
                        res["secret"] = self.__decode(res.get("secret", ""))
            except Exception as e:
                print("find_by_name", e)
            return res

    def __decode(self, secret_base64):
        secret = base64.b64decode(secret_base64)
        secret_decoded = secret.decode("ascii")
        return secret_decoded

    def __encode(self, text):
        message_bytes = text.encode("ascii")
        base64_bytes = base64.b64encode(message_bytes)
        secret_base64 = base64_bytes.decode("ascii")
        return secret_base64

    async def list(self, uid):
        data = []
        try:
            async with self.__storage_sem:
                self.__load_secrets(uid)
                data = self.__df.to_dict("records")
                for row in data:
                    row["secret"] = self.__decode(row.get("secret", ""))
        except Exception as e:
            print("list", e)
        return data

    def __delete(self, cur_elem, uid, name):
        self.__logger.info(
            {
                "id": uid,
                "type": t_secret,
                "value": name,
                "status": t_delete,
                "params": {},
            }
        )
        self.__df = self.__df.drop(cur_elem.index)

    def __add(self, uid, name, secret):
        now = datetime.datetime.now(tz=pytz.timezone(n_env.tz))
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.__logger.info(
            {
                "id": uid,
                "type": t_secret,
                "value": name,
                "status": t_add,
                "params": {},
            }
        )
        new_row = {
            "id": uid,
            "name": name,
            "secret": self.__encode(secret),
            "lastUpdate": dt_string,
        }
        cur_df = self.__df.to_dict("records")
        if len(self.__df) > 0:
            self.__df = pd.DataFrame([*cur_df, new_row])
        else:
            self.__df = pd.DataFrame([new_row])

    def __update(self, cur_elem, uid, name, secret, status):
        now = datetime.datetime.now(tz=pytz.timezone(n_env.tz))
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.__logger.info(
            {
                "id": uid,
                "type": t_secret,
                "value": name,
                "status": t_update,
                "params": {},
            }
        )
        index = cur_elem.index[0]
        self.__df.at[index, "id"] = uid
        self.__df.at[index, "secret"] = self.__encode(secret)
        self.__df.at[index, "lastUpdate"] = dt_string

        if status != t_add:
            return t_update
        return t_add

    async def update(self, uid, name, secret, status):
        data = None
        res = t_error
        async with self.__storage_sem:
            try:
                cur_elem = self.__df[self.__df.name == name]
                if len(cur_elem) > 1:
                    self.__logger.error(
                        {
                            "id": uid,
                            "type": t_secret,
                            "value": name,
                            "status": t_error,
                            "params": {},
                            "error": "Already exist multiple time",
                        }
                    )
                    return {
                        "status": t_error,
                        "id": uid,
                        "data": [],
                        "error": f"{name} already exist multiple time",
                    }
                if len(cur_elem) == 1:
                    if status == t_delete:
                        self.__delete(cur_elem, uid, name)
                    else:
                        res = self.__update(cur_elem, uid, name, secret, status)
                elif status == t_add and len(cur_elem) == 0:
                    self.__add(uid, name, secret)
                else:
                    res = t_skip
            except Exception as e:
                print("cannot update", e)
                self.__logger.error(
                    {
                        "id": uid,
                        "type": t_secret,
                        "value": name,
                        "status": t_error,
                        "params": {},
                        "error": str(e),
                    }
                )
                raise ServerError({"id": uid, "error": str(e)}, status_code=500)
            data = self.__df.to_dict("records")
            self.__save_to_file(uid, data)
        return {"id": uid, "status": res, "data": data}
