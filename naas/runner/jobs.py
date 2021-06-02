from sanic.exceptions import ServerError
from .env_var import cpath, n_env
from asyncio import Semaphore
from naas.ntypes import (
    t_delete,
    t_add,
    t_skip,
    t_update,
    t_job,
    t_error,
    t_health,
    t_start,
    t_notebook,
    t_asset,
    t_output,
    t_dependency,
    t_scheduler,
    t_list,
    t_send,
)
import pandas as pd
import datetime
import errno
import json
import uuid
import pytz
import os

filters = [t_notebook, t_asset, t_dependency, t_scheduler]
filters_api = [t_notebook, t_asset]


class Jobs:
    __storage_sem = None
    __df = None
    __logger = None
    __json_name = "jobs.json"
    __colums = [
        "id",
        "type",
        "value",
        "path",
        "status",
        "params",
        "lastUpdate",
        "lastRun",
        "runs",
    ]

    def __init__(self, logger, clean=False, init_data=[]):
        self.__json_secrets_path = os.path.join(
            n_env.path_naas_folder, self.__json_name
        )
        self.__storage_sem = Semaphore(1)
        self.__logger = logger
        if not os.path.exists(n_env.path_naas_folder):
            try:
                print("Init Naas folder Jobs")
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
                        "status": t_error,
                        "error": str(e),
                    }
                )
        else:
            uid = str(uuid.uuid4())
            self.__df = self.__get_save_from_file(uid)
        self.__cleanup_jobs()

    def reload_jobs(self):
        uid = str(uuid.uuid4())
        self.__df = self.__get_save_from_file(uid)
        self.__cleanup_jobs()

    def __cleanup_jobs(self):
        try:
            if self.__df is None or len(self.__df) == 0:
                self.__df = pd.DataFrame(columns=self.__colums)
            if len(self.__df) > 0:
                self.__df = self.__df[self.__df.type.isin(filters)]
                self.__dedup_jobs()
        except Exception as err:
            print("Cannot cleanup", err)

    async def move_job(self, uid, old_path, new_path):
        async with self.__storage_sem:
            try:
                if len(self.__df) > 0:
                    cur_elems = self.__df.query(f'path == "{old_path}"')
                    new_elems = self.__df.query(f'path == "{new_path}"')
                    if len(cur_elems.index) == 0:
                        return {"status": t_skip, "error": "job not found"}
                    elif len(new_elems.index) != 0:
                        return {"status": t_skip, "error": "new job path exist"}
                    index = cur_elems.index[0]
                    self.__df.at[index, "path"] = new_path
                    data = self.__df.to_dict("records")
                    try:
                        os.makedirs(os.path.dirname(new_path))
                    except OSError:
                        pass
                    filename = os.path.basename(old_path)
                    dirname = os.path.dirname(old_path)
                    new_filename = os.path.basename(new_path)
                    os.rename(old_path, new_path)
                    moved = [{"from": cpath(old_path), "to": cpath(new_path)}]
                    for ffile in os.listdir(dirname):
                        if ffile.endswith(f"__{filename}"):
                            tmp_path = os.path.join(dirname, ffile)
                            start = ffile.replace(filename, "")
                            new_tmp_path = new_path.replace(
                                new_filename, f"{start}{new_filename}"
                            )
                            moved.append(
                                {"from": cpath(tmp_path), "to": cpath(new_tmp_path)}
                            )
                            os.rename(tmp_path, new_tmp_path)
                    self.__save_to_file(uid, data)
                    return {"status": t_send, "data": moved}
            except Exception as e:
                print("move_job", e)
                return {"status": t_error, "error": str(e)}

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
            f = open(self.__json_secrets_path, "r")
            data_l = json.load(f)
            f.close()
            # data = data_l
            dt_string = datetime.datetime.now(tz=pytz.timezone(n_env.tz)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            for d in data_l:
                # Fix formating of old jobs
                runs = d.get("runs", [])
                if type(runs) != list:
                    try:
                        runs = json.loads(runs)
                    except Exception:
                        runs = []
                        pass
                c = {
                    "id": d.get("id", uid),
                    "type": d.get("type", ""),
                    "value": d.get("value", ""),
                    "path": d.get("path", ""),
                    "status": d.get("status", t_update),
                    "params": d.get("params", {}),
                    "lastUpdate": d.get("lastUpdate", dt_string),
                    "lastRun": d.get("lastRun", 0),
                    "runs": runs,
                }
                data.append(c)
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

    async def find_by_path(self, uid, filepath, target_type=None):
        res = None
        async with self.__storage_sem:
            try:
                if len(self.__df) > 0:
                    if target_type:
                        cur_jobs = self.__df[
                            (self.__df.type == target_type)
                            & (self.__df.path.str.lower() == filepath.lower())
                        ]
                    else:
                        cur_jobs = self.__df[(self.__df.path == filepath)]
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

    def __match_clear(self, cur_filename, filename, clear_all):
        if (
            clear_all
            and cur_filename.endswith(f"__{filename}")
            or cur_filename == filename
        ):
            return True
        else:
            return False

    def clear_file(self, uid, path, histo, mode=None):
        # possible format
        # histo___filename
        # output__filename
        # histo___output__filename
        try:
            filename = os.path.basename(path)
            clear_all = False
            if mode:
                filename = f"{mode}__{filename}"
            if histo and histo == "all":
                clear_all = True
            elif histo:
                filename = f"{histo}___{filename}"
            removed = []
            dirname = os.path.dirname(path)
            if os.path.exists(path):
                for ffile in os.listdir(dirname):
                    if self.__match_clear(ffile, filename, clear_all):
                        tmp_path = os.path.join(dirname, ffile)
                        os.remove(tmp_path)
                        tmp_path = cpath(tmp_path)
                        removed.append(tmp_path)
                        self.__logger.info(
                            {
                                "id": uid,
                                "filename": filename,
                                "histo": histo,
                                "type": "clear_file",
                                "status": t_delete,
                                "filepath": path,
                            }
                        )
            return {"id": uid, "status": t_health, "data": removed}
        except Exception as e:
            print("clear_file", e)
            return {"id": uid, "status": t_error, "error": str(e)}

    def list_files(self, uid, path, filetype, output=False):
        d = []
        dirname = os.path.dirname(path)
        filename = os.path.basename(path)
        # if output:
        #     filename = f"output_{filetype}_{filename}"
        # else:
        #     filename = f"{filetype}_{filename}"
        if output:
            filename = f"___{t_output}__{filename}"
        else:
            filename = f"___{filename}"
        for ffile in os.listdir(dirname):
            if ffile.endswith(filename):
                split_list = ffile.split("___")
                histo = split_list[0]
                tmp_path = os.path.join(dirname, ffile)
                tmp_path = cpath(tmp_path)
                d.append({"timestamp": histo, "filepath": tmp_path})
        self.__logger.info(
            {
                "id": uid,
                "type": "list_files",
                "filename": filename,
                "status": t_list,
                "filepath": path,
            }
        )
        return d

    async def list(self, uid, as_df=False, prodPath=False):
        data = []
        try:
            async with self.__storage_sem:
                if as_df:
                    data = self.__df.copy()
                    data["path"] = data["path"] if prodPath else cpath(data["path"])
                else:
                    data = self.__df.to_dict("records")
                    for d in data:
                        try:
                            d["path"] = d["path"] if prodPath else cpath(d["path"])
                            d["runs"] = json.loads(d.get("runs", "[]"))
                        except Exception:
                            d["runs"] = []
                            pass
        except Exception as e:
            print("list", e)
        return data

    def __delete(self, cur_elem, uid, path, target_type, value, params):
        try:
            dt_string = datetime.datetime.now(tz=pytz.timezone(n_env.tz)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
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
            index = cur_elem.index[0]
            self.__df.at[index, "id"] = uid
            self.__df.at[index, "status"] = t_delete
            self.__df.at[index, "lastUpdate"] = dt_string
            return t_delete
        except Exception as e:
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
            return t_error

    def __add(self, uid, path, target_type, value, params, run_time):
        try:
            dt_string = datetime.datetime.now(tz=pytz.timezone(n_env.tz)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self.__logger.info(
                {
                    "id": uid,
                    "type": target_type,
                    "value": value,
                    "status": t_add,
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
                "lastRun": run_time,
                "runs": json.dumps([]),
                "lastUpdate": dt_string,
            }
            cur_df = self.__df.to_dict("records")
            if len(self.__df) > 0:
                self.__df = pd.DataFrame([*cur_df, new_row])
            else:
                self.__df = pd.DataFrame([new_row])
            return t_add
        except Exception as e:
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
            return t_error

    def __update(self, cur_elem, uid, path, value, params, status, run_time):
        now = datetime.datetime.now(tz=pytz.timezone(n_env.tz))
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        self.__logger.info(
            {
                "id": uid,
                "type": t_job,
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
        if run_time > 0:
            try:
                runs = json.loads(self.__df.at[index, "runs"])
            except Exception:
                runs = []
                pass
            runs.append(
                {"id": uid, "duration": run_time, "date": dt_string, "status": status}
            )
            self.__df.at[index, "runs"] = json.dumps(runs)
            self.__df.at[index, "lastRun"] = run_time
        return t_update

    async def update(self, uid, path, target_type, value, params, status, run_time=0):
        data = None
        res = t_error
        async with self.__storage_sem:
            try:
                cur_elem = self.__df.query(
                    f'type == "{target_type}" and path == "{path}"'
                )
                if len(cur_elem) == 1 and status == t_delete:
                    res = self.__delete(cur_elem, uid, path, target_type, value, params)
                elif len(cur_elem) == 1:
                    res = self.__update(
                        cur_elem,
                        uid,
                        path,
                        value,
                        params,
                        status,
                        run_time,
                    )
                elif len(cur_elem) == 0 and status == t_add:
                    res = self.__add(uid, path, target_type, value, params, run_time)
                else:
                    res = t_skip
                if res == t_error:
                    raise ServerError(
                        {
                            "status": t_error,
                            "id": uid,
                            "data": [],
                            "error": "unknow error",
                        },
                        status_code=500,
                    )
                data = self.__df.to_dict("records")
                self.__save_to_file(uid, data)
                return {"id": uid, "status": res, "data": data}
            except Exception as e:
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
                raise ServerError(
                    {"status": t_error, "id": uid, "data": [], "error": str(e)},
                    status_code=500,
                )
