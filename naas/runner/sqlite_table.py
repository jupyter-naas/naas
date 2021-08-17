import sqlite3
import pandas as pd
import os
import errno


class SqliteTable:
    __columns = []
    __file_name = ""
    __db = None
    __focused_table = ""

    def __init__(self, cols=[], file="logs.db", table="logs"):
        self.__columns = cols
        self.__file_name = file
        self.__create_connection()
        self.create_table(table)

    def __get_csv_values(self, csv_file):
        return pd.read_csv(csv_file, sep=";")

    def __create_connection(self):
        folder = os.path.dirname(self.__file_name)
        if not os.path.exists(folder):
            try:
                print("Init Sqlite folder")
                os.makedirs(folder)
            except OSError as exc:  # Guard against race condition
                print("__path_sql_files", folder)
                if exc.errno != errno.EEXIST:
                    raise
            except Exception as e:
                print("Exception", e)
        try:
            self.__db = sqlite3.connect(self.__file_name)
        except Exception as e:
            print(e)

    def execute_command(self, command, commit=True, **kwargs):
        ret = None
        if self.__db:
            try:
                cursor = self.__db.cursor()
                cursor.execute(command, kwargs)
                if commit:
                    cursor.execute("COMMIT")
            except Exception as e:
                print(e)
                return e
        return ret

    def clear(self):
        self.execute_command(f"DELETE FROM {self.__focused_table}")

    def search_in_db(self, value="", table="", columns=None):
        if table == "":
            table = self.__focused_table
        if columns is None:
            columns = self.__columns
        col = ""
        for c in columns:
            if col != "":
                col += " or "
            col += f"{c} like " + "'%" + value + "%'"
        try:
            cursor = self.__db.cursor()
            cursor.execute(f"SELECT * FROM {table} WHERE {col}")
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return []

    def add_on_table(self, commit=True, table="", **kwargs):
        keys = []
        values = []
        if table == "":
            table = self.__focused_table

        for k, v in kwargs.items():
            keys.append(k)
            values.append(f":{k}")
            if type(v) in [dict, object, list]:
                kwargs[k] = str(kwargs[k])

        cmd = f"INSERT INTO {table} ({','.join(keys)}) VALUES ({','.join(values)})"
        return self.execute_command(cmd, commit=commit, **kwargs)

    def get_db_content(self, table=""):
        if table == "":
            table = self.__focused_table
        try:
            cursor = self.__db.cursor()
            cursor.execute(f"SELECT * FROM {table}")
            return cursor.fetchall()
        except Exception as e:
            print(e)
            return []

    def csv_to_sql(self, csv_file):
        try:
            df = self.__get_csv_values(csv_file)
            for index, row in df.iterrows():
                data = {}
                for col in self.__columns:
                    data[col] = row[col]
                self.add_on_table(commit=False, **data)
            self.__db.cursor().execute("Commit")
        except Exception as e:
            print(e)

    def create_table(self, table):
        columns = ""
        self.__focused_table = table
        for col in self.__columns:
            try:
                columns += "" if columns == "" else ","
                columns += col + " TEXT"
            except Exception as e:
                print(e)
        self.execute_command(
            f"CREATE TABLE IF NOT EXISTS {table} ({columns})", commit=False
        )
