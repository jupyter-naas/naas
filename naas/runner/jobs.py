from asyncio import Semaphore
from naas.types import (
    t_delete,
    t_add,
    t_skip,
    t_update,
    t_error,
    t_start,
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


filters = [t_notebook, t_asset, t_dependency, t_scheduler]
filters_api = [t_notebook, t_asset]


class Jobs:
    __storage_sem = None
    __path_user_files = None
    __df = None
    __logger = None
    __naas_folder = ".naas"
    __json_name = "jobs.json"

    def __init__(self, logger, clean=False, init_data=[]):
        self.__path_user_files = os.environ.get(
            "JUPYTER_SERVER_ROOT", f'/home/{os.environ.get("NB_USER", "ftp")}'
        )
        self.__path_naas_files = os.path.join(
            self.__path_user_files, self.__naas_folder
        )
        self.__json_secrets_path = os.path.join(
            self.__path_naas_files, self.__json_name
        )
        self.__storage_sem = Semaphore(1)
        self.__logger = logger
        if not os.path.exists(self.__path_naas_files):
            try:
                print("Init Naas folder Jobs")
                os.makedirs(self.__path_naas_files)
            except OSError as exc:  # Guard against race condition
                print("__path_naas_files", self.__path_naas_files)
                if exc.errno != errno.EEXIST:
                    raise
            except Exception as e:
                print("Exception", e)
        if not os.path.exists(self.__json_secrets_path) or clean:
            uid = str(uuid.uuid4())
            try:
                print("Init Job Storage", self.__json_secrets_path)
                self.__save_to_file(uid, init_data)
                self.__df = None
            except Exception as e:
                print("Exception", e)
                self.__logger.error(
                    {
                        "id": uid,
                        "type": "init_job_storage",
                        "filepath": self.__json_secrets_path,
                        "status": "error",
                        "error": str(e),
                    }
                )
        else:
            uid = str(uuid.uuid4())
            self.__df = self.__get_save_from_file(uid)
            self.__cleanup_jobs()
        if self.__df is None or len(self.__df) == 0:
            self.__df = pd.DataFrame(
                columns=[
                    "id",
                    "type",
                    "value",
                    "path",
                    "status",
                    "params",
                    "lastUpdate",
                    "lastRun",
                    "nbRun",
                    "totalRun",
                ]
            )

    def __cleanup_jobs(self):
        if len(self.__df) > 0:
            self.__df = self.__df[self.__df.type.isin(filters)]
            self.__dedup_jobs()

    def __dedup_jobs(self):
        new_df = self.__df[
            (self.__df.type != t_notebook) & (self.__df.type != t_asset)
        ].to_dict("records")
        cur_notebook = self.__df[self.__df.type == t_notebook]
        cur_asset = self.__df[self.__df.type == t_asset]
        cur_asset = cur_asset.drop_duplicates(subset=["value"]).to_dict("records")
        cur_notebook = cur_notebook.drop_duplicates(subset=["value"]).to_dict("records")
        self.__df = pd.DataFrame([*new_df, *cur_asset, *cur_notebook])
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
                    "status": "exception",
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
                    "status": "exception",
                    "filepath": self.__json_secrets_path,
                    "error": str(err),
                }
            )

    async def find_by_value(self, uid, value, target_type):
        res = None
        async with self.__storage_sem:
            try:
                if len(self.__df) > 0:
                    cur_jobs = self.__df[
                        (self.__df.type == target_type) & (self.__df.value == value)
                    ]
                    cur_job = cur_jobs.to_dict("records")
                    if len(cur_job) > 0:
                        res = cur_job[0]
            except Exception as e:
                print("find_by_value", e)
            return res

    async def find_by_path(self, uid, filepath, target_type):
        res = None
        async with self.__storage_sem:
            try:
                if len(self.__df) > 0:
                    cur_jobs = self.__df[
                        (self.__df.type == target_type) & (self.__df.path == filepath)
                    ]
                    cur_job = cur_jobs.to_dict("records")
                    if len(cur_job) > 0:
                        res = cur_job[0]
            except Exception as e:
                print("find_by_path", e)
            return res

    async def is_running(self, uid, notebook_filepath, target_type):
        res = False
        try:
            cur_job = await self.find_by_path(uid, notebook_filepath, target_type)
            if cur_job:
                status = cur_job.get("status", None)
                if status and status == t_start:
                    res = True
        except Exception as e:
            print("is_running", e)
        return res

    async def list(self, uid):
        data = []
        try:
            async with self.__storage_sem:
                data = self.__df.to_dict("records")
        except Exception as e:
            print("list", e)
        return data

    def __delete(self, cur_elem, uid, path, target_type, value, params):
        self.__logger.info(
            {
                "id": uid,
                "type": target_type,
                "value": value,
                "status": t_delete,
                "filepath": path,
                "params": params,
            }
        )
        self.__df = self.__df.drop(cur_elem.index)

    def __add(self, uid, path, target_type, value, params, run_time):
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.__logger.info(
            {
                "id": uid,
                "type": target_type,
                "value": value,
                "status": t_update,
                "filepath": path,
                "params": params,
            }
        )
        new_row = {
            "id": uid,
            "type": target_type,
            "value": value,
            "status": t_add,
            "path": path,
            "params": params,
            "nbRun": 1 if run_time > 0 else 0,
            "lastRun": run_time,
            "totalRun": run_time,
            "lastUpdate": dt_string,
        }
        cur_df = self.__df.to_dict("records")
        if len(self.__df) > 0:
            self.__df = pd.DataFrame([*cur_df, new_row])
        else:
            self.__df = pd.DataFrame([new_row])

    def __update(
        self, cur_elem, uid, path, target_type, value, params, status, run_time
    ):
        now = datetime.datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.__logger.info(
            {
                "id": uid,
                "type": target_type,
                "value": value,
                "status": t_update,
                "filepath": path,
                "params": params,
            }
        )
        index = cur_elem.index[0]
        self.__df.at[index, "id"] = uid
        self.__df.at[index, "status"] = status
        self.__df.at[index, "value"] = value
        self.__df.at[index, "params"] = params
        self.__df.at[index, "lastUpdate"] = dt_string
        if run_time > 0 and status != t_add:
            self.__df.at[index, "nbRun"] = self.__df.at[index, "nbRun"] + 1
            self.__df.at[index, "lastRun"] = run_time
            total_run = float(self.__df.at[index, "totalRun"])
            self.__df.at[index, "totalRun"] = run_time + total_run
            return t_update
        elif status == t_add:
            self.__df.at[index, "nbRun"] = 0
            self.__df.at[index, "lastRun"] = 0
            self.__df.at[index, "totalRun"] = 0
            return t_add

    async def update(self, uid, path, target_type, value, params, status, run_time=0):
        data = None
        res = t_error
        async with self.__storage_sem:
            try:
                cur_elem = self.__df[
                    (self.__df.type == target_type) & (self.__df.path == path)
                ]
                dup_elem = self.__df[
                    (self.__df.path != path)
                    & (self.__df.type == target_type)
                    & (self.__df.value == value)
                ]
                if len(dup_elem) > 0 and target_type in filters_api:
                    self.__logger.error(
                        {
                            "id": uid,
                            "type": target_type,
                            "value": value,
                            "status": t_error,
                            "filepath": path,
                            "params": params,
                            "error": "Already exist",
                        }
                    )
                    return {
                        "status": "error",
                        "id": uid,
                        "data": [],
                        "error": f"type {target_type} with key {value} already exist",
                    }
                if len(cur_elem) == 1:
                    if status == t_delete:
                        self.__delete(cur_elem, uid, path, target_type, value, params)
                    else:
                        res = self.__update(
                            cur_elem,
                            uid,
                            path,
                            target_type,
                            value,
                            params,
                            status,
                            run_time,
                        )
                elif status == t_add and len(cur_elem) == 0:
                    self.__add(uid, path, target_type, value, params, run_time)
                else:
                    res = t_skip
            except Exception as e:
                print("cannot update", e)
                self.__logger.error(
                    {
                        "id": uid,
                        "type": target_type,
                        "value": value,
                        "status": t_error,
                        "filepath": path,
                        "params": params,
                        "error": str(e),
                    }
                )
                raise ServerError({"id": uid, "error": str(e)}, status_code=500)
            data = self.__df.to_dict("records")
            self.__save_to_file(uid, data)
        return {"id": uid, "status": res, "data": data}
