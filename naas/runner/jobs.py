from asyncio import Semaphore
from naas.types import t_delete, t_add, t_skip, t_update, t_error, t_start
import pandas as pd
import datetime
import errno
import json
import os
import uuid


class Jobs:
    __storage_sem = None
    __path_user_files = None
    __df = None
    __logger = None
    __naas_folder = ".naas"
    __json_name = "jobs.json"

    def __init__(self, logger, loop, clean=False, init_data=[]):
        self.__path_user_files = os.environ.get(
            "JUPYTER_SERVER_ROOT", f'/home/{os.environ.get("NB_USER", "ftp")}'
        )
        self.__path_naas_files = os.path.join(
            self.__path_user_files, self.__naas_folder
        )
        self.__json_secrets_path = os.path.join(
            self.__path_naas_files, self.__json_name
        )
        self.__storage_sem = Semaphore(1, loop=loop)
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
            except Exception as e:
                print("Exception", e)
                self.__logger.error(
                    {
                        "id": uid,
                        "type": "init_job_storage",
                        "status": "error",
                        "error": str(e),
                    }
                )
        else:
            uid = str(uuid.uuid4())
            self.__df = self.__get_save_from_file(uid)
            if len(self.__df) == 0:
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
                        "totalRun",
                    ]
                )

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
        return pd.DataFrame(data)

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
                    if len(cur_job) == 1:
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
                    if len(cur_job) == 1:
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
                print("list acquire", uid)
                data = self.__df.to_dict("records")
        except Exception as e:
            print("list", e)
        return data

    async def update(self, uid, path, target_type, value, params, status, runTime=0):
        data = None
        res = t_error
        async with self.__storage_sem:
            try:
                res = status
                cur_elem = self.__df[
                    (self.__df.type == target_type) & (self.__df.path == path)
                ]
                now = datetime.datetime.now()
                dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
                if len(cur_elem) == 1:
                    if status == t_delete:
                        self.__logger.info(
                            {
                                "id": uid,
                                "type": target_type,
                                "value": value,
                                "status": t_delete,
                                "path": path,
                                "params": params,
                            }
                        )
                        self.__df = self.__df.drop(cur_elem.index)
                    else:
                        self.__logger.info(
                            {
                                "id": uid,
                                "type": target_type,
                                "value": value,
                                "status": t_update,
                                "path": path,
                                "params": params,
                            }
                        )
                        index = cur_elem.index[0]
                        self.__df.at[index, "id"] = uid
                        self.__df.at[index, "status"] = status
                        self.__df.at[index, "value"] = value
                        self.__df.at[index, "params"] = params
                        self.__df.at[index, "lastUpdate"] = dt_string
                        if runTime > 0 and status != t_add:
                            self.__df.at[index, "lastRun"] = runTime
                            self.__df.at[index, "totalRun"] = runTime + (
                                self.__df.at[index, "totalRun"]
                                if self.__df.at[index, "totalRun"]
                                else 0
                            )
                        elif status == t_add:
                            self.__df.at[index, "lastRun"] = 0
                            self.__df.at[index, "totalRun"] = 0
                        res = t_update
                elif status == t_add and len(cur_elem) == 0:
                    self.__logger.info(
                        {
                            "id": uid,
                            "type": target_type,
                            "value": value,
                            "status": t_update,
                            "path": path,
                            "params": params,
                        }
                    )
                    new_row = [
                        {
                            "id": uid,
                            "type": target_type,
                            "value": value,
                            "status": t_add,
                            "path": path,
                            "params": params,
                            "lastRun": runTime,
                            "totalRun": runTime,
                            "lastUpdate": dt_string,
                        }
                    ]
                    df_new = pd.DataFrame(new_row)
                    self.__df = pd.concat([self.__df, df_new], axis=0)
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
                        "path": path,
                        "params": params,
                        "error": str(e),
                    }
                )
            data = self.__df.to_dict("records")
            self.__save_to_file(uid, data)
            print("release =>\n\n")
        return {"status": res, "data": data}
