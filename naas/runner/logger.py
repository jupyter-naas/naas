import pandas as pd
import traceback
import logging
import errno
import json
import csv
import io
import os
import datetime as dt


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
        self.writer.writerow(
            [record.asctime, record.levelname, record.name, record.msg]
        )
        data = self.output.getvalue()
        self.output.truncate(0)
        self.output.seek(0)
        return data.strip()


class Logger:
    __log = None
    __name = "naas_logger"
    __logs_filename = "logs.csv"
    __naas_folder = ".naas"
    __path_user_files = None
    __columns = ["asctime", "levelname", "name", "message"]

    def __init__(self, clear=False):
        self.__path_user_files = os.environ.get(
            "JUPYTER_SERVER_ROOT", f'/home/{os.environ.get("NB_USER", "ftp")}'
        )
        self.__path_naas_files = os.path.join(
            self.__path_user_files, self.__naas_folder
        )
        self.__path_logs_file = os.path.join(
            self.__path_naas_files, self.__logs_filename
        )
        if not os.path.exists(self.__path_logs_file):
            try:
                print("Init Naas folder Logger")
                os.makedirs(self.__path_naas_files)
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
        self.__log.info(json.dumps(data))

    def error(self, data):
        self.__log.error(json.dumps(data))

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
    ):
        df = None
        try:
            df = pd.read_csv(
                self.__path_logs_file, sep=";", usecols=self.__columns, index_col=0
            )
            df1 = pd.DataFrame(
                df.pop("message").apply(pd.io.json.loads).values.tolist(),
                index=df.index,
            )
            df = pd.concat([df1, df], axis=1, sort=False)
            if len(filters) > 0:
                df = df[df.type.isin(filters)]
            total_records = len(df.index)
            if search and search != "":
                idx = df.apply(
                    lambda ts: any(ts.str.contains(search, na=False, regex=False)),
                    axis=1,
                )
                df = df[idx]
            if skip > 0:
                df = df.iloc[skip:]
            if limit > 0:
                df = df[:limit]
            df = df.reset_index()
            return {
                "data": json.loads(df.to_json(orient="records")),
                "totalRecords": total_records,
            }
        except Exception as e:
            tb = traceback.format_exc()
            print("list logs", e, tb)
            return {"data": [], "totalRecords": 0}
