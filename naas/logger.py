import pandas as pd
import logging
import json
import csv
import io
import os

class CsvFormatter(logging.Formatter):
    """
    Custom logger for the csv logs
    """

    def __init__(self):
        super().__init__(datefmt='%Y-%m-%d %H:%M:%S')
        self.output = io.StringIO()
        self.writer = csv.writer(
            self.output, delimiter=';', quoting=csv.QUOTE_ALL)
        self.writer.writerow(
            ['asctime', 'levelname', 'funcName', 'lineno', 'message'])

    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        self.writer.writerow(
            [record.asctime, record.levelname, record.funcName, record.lineno, record.msg])
        data = self.output.getvalue()
        self.output.truncate(0)
        self.output.seek(0)
        return data.strip()

class Logger():
    log = None
    __name = 'naas_logger'
    __logs_filename = 'logs.csv'
    __naas_file = '.nass'
    __path_user_files = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
    
    def __init__(self):
        self.__path_naas_files = os.path.join(self.__path_user_files, self.__naas_file)
        self.__path_logs_file = os.path.join(self.__path_naas_files, self.__logs_filename) 
        self.log = logging.getLogger(self.__name)
        handler = logging.FileHandler(self.__path_logs_file, "w")
        handler.setFormatter(CsvFormatter())
        self.log.addHandler(handler)
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(process)s %(module)s - %(funcName)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        self.write = self.log

    def get_file_path(self):
        return self.__path_logs_file
    
    def get(self, uid: str, skip: int = 0, limit: int = 0, search: str = '', filters: list = None):
        df = None
        try:
            df = pd.read_csv(self.__path_logs_file, sep=';', index_col=0)
            df1 = pd.DataFrame(df.pop('message').apply(
                pd.io.json.loads).values.tolist(), index=df.index)
            df = df.join(df1)
            if filters:
                df = df[df.type.isin(filters)]
            totalRecords = len(df.index)
            if search != '':
                idx = df.apply(lambda ts: any(ts.str.contains(
                    search, na=False, regex=False)), axis=1)
                df = df[idx]
            if skip > 0:
                df = df.iloc[skip:]
            if limit > 0:
                df = df[:limit]
            df = df.reset_index()
            return {'data': json.loads(df.to_json(orient='records')), 'totalRecords': totalRecords}
        except Exception as e:
            print (e)
            return {'data': 'error', 'totalRecords': 0}
            
    
