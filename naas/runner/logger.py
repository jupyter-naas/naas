from .env_var import n_env
import datetime as dt
import pandas as pd
import traceback
import logging
import errno
import json
import csv
import io
import os


class CsvFormatter(logging.Formatter):
    """
    Custom logger for the csv logs
    """

    converter = dt.datetime.fromtimestamp

    def __init__(self):
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S.%f")
        self.output = io.StringIO()
        self.writer = csv.writer(self.output, delimiter=";", quoting=csv.QUOTE_ALL)

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            t = ct.strftime("%Y-%m-%d %H:%M:%S")
            s = "%s,%03d" % (t, record.msecs)
        return s

    def format(self, record):
        print("record", record)
        record.asctime = self.formatTime(record, self.datefmt)
        try:
            data = json.loads(record.msg or "{}")
            if type(data) != dict:
                data = {"status": data}
        except ValueError:
            data = {"status": record.msg}
        record.id = data.get("id", "")
        record.type = data.get("type", "")
        record.filepath = data.get("filepath", "")
        record.status = data.get("status", "")
        record.error = data.get("error", "")

        self.writer.writerow(
            [
                record.asctime,
                record.levelname,
                record.name,
                record.id,
                record.type,
                record.filepath,
                record.status,
                record.error,
            ]
        )
        data = self.output.getvalue()
        self.output.truncate(0)
        self.output.seek(0)
        return data.strip()


class Logger:
    __log = None
    __name = "naas_logger"
    __logs_filename = "logs.csv"
    __columns = [
        "asctime",
        "levelname",
        "name",
        "id",
        "type",
        "filepath",
        "status",
        "error",
    ]

    def __init__(self, clear=False):
        self.__path_logs_file = os.path.join(
            n_env.path_naas_folder, self.__logs_filename
        )
        if not os.path.exists(self.__path_logs_file):
            try:
                print("Init Naas folder Logger")
                os.makedirs(n_env.path_naas_folder)
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        if clear or not os.path.exists(self.__path_logs_file):
            self.clear()
        self.__log = logging.getLogger(self.__name)
        handler = logging.FileHandler(self.__path_logs_file, "a")
        handler.setFormatter(CsvFormatter())
        self.__log.addHandler(handler)
        logging.basicConfig(level=logging.INFO)

    def info(self, data):
        print("info", data, self.__path_logs_file)
        message = ""
        try:
            message = json.dumps(data)
        except ValueError:
            message = str(data)
        self.__log.info(message)

    def error(self, data):
        message = ""
        try:
            message = json.dumps(data)
        except ValueError:
            message = str(data)
        self.__log.error(message)

    def clear(self):
        with open(self.__path_logs_file, "w") as fp:
            separator = ";"
            fp.write(f"{separator.join(self.__columns)}\n")

    def get_file_path(self):
        return self.__path_logs_file

    def list(
        self,
        uid: str,
        skip: int = 0,
        limit: int = 0,
        search: str = "",
        filters: list = [],
        sort: list = [],
    ):
        df = None
        try:
            df = pd.read_csv(
                self.__path_logs_file,
                sep=";",
                usecols=self.__columns,
                index_col=0,
                error_bad_lines=False,
                quoting=csv.QUOTE_ALL,
            )
            if len(filters) > 0:
                df = df[df.type.isin(filters)]
            if len(sort) > 0:
                for query in sort:
                    field = [query["field"]]
                    ascending = False if query["type"] == "desc" else True
                    df = df.sort_values(by=field, ascending=ascending)
            total_records = len(df.index)
            if search and search != "":
                idx = df.apply(
                    lambda ts: any(ts.str.contains(search, na=False, regex=False)),
                    axis=1,
                    raw=False,
                    result_type="broadcast",
                )
                df = df[idx.id]
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
