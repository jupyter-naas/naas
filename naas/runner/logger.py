from .env_var import n_env
import datetime as dt
import pandas as pd
import traceback
import json
import os

from .sqlite_table import SqliteTable


class Logger:
    __sql = None
    __name = "naas_logger"
    __logs_file = n_env.path_naas_folder + "/logs.db"
    __logs_csv_file = n_env.path_naas_folder + "/logs.csv"
    __date_format = "%Y-%m-%d %H:%M:%S.%f"
    __columns = [
        "asctime",
        "levelname",
        "name",
        "id",
        "type",
        "filename",
        "histo",
        "filepath",
        "output_filepath",
        "status",
        "error",
        "traceback",
        "duration",
        "url",
        "params",
        "token",
        "value",
        "main_id",
        "search",
    ]

    def __init__(self, clear=False):
        file_creation = not os.path.exists(self.__logs_file)
        #        is_csv = os.path.exists(self.__logs_csv_file)
        print("Init Naas logger")
        self.__sql = SqliteTable(self.__columns, self.__logs_file)
        if not file_creation and clear:
            self.__sql.clear()

    #        if file_creation and is_csv and not clear:
    #            self.__sql.csv_to_sql(self.__logs_csv_file)
    #            os.remove(self.__logs_csv_file)

    def add_log(self, **kwargs):
        kwargs["asctime"] = dt.datetime.now().strftime(self.__date_format)
        kwargs["name"] = self.__name
        return self.__sql.add_on_table(commit=True, **kwargs)

    def info(self, data):
        data["levelname"] = "INFO"
        return self.add_log(**data)

    def error(self, data):
        data["levelname"] = "ERROR"
        return self.add_log(**data)

    def clear(self):
        self.__sql.clear()

    def get_file_path(self):
        return self.__logs_file

    def list(
        self,
        uid: str,
        skip: int = 0,
        limit: int = 0,
        search: str = "",
        filters: list = [],
        sort: list = [],
        technical_rows: bool = True,
    ):
        df = None
        try:
            df = pd.DataFrame(
                data=self.__sql.search_in_db(search), index=None, columns=self.__columns
            )
            if not technical_rows and "type" in df and "filepath" in df:
                df = df[df["type"] != df["filepath"]]
                df = df[df["status"] != "busy"]
            if len(filters) > 0:
                df = df[df.type.isin(filters)]
            if len(sort) > 0:
                for query in sort:
                    field = [query["field"]]
                    ascending = False if query["type"] == "desc" else True
                    df = df.sort_values(by=field, ascending=ascending)
            total_records = len(df.index)
            if skip > 0:
                df = df.iloc[skip:]
            if limit > 0:
                df = df[:limit]
            df = df.reset_index()
            return {
                "uid": uid,
                "data": json.loads(df.to_json(orient="records")),
                "totalRecords": total_records,
            }
        except Exception as e:
            tb = traceback.format_exc()
            print("list logs", e, tb)
            return {"uid": uid, "data": [], "totalRecords": 0}
