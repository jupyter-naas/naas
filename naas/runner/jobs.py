# from gevent.lock import BoundedSemaphore
from asyncio import Semaphore
from naas.types import t_delete, t_add, t_skip, t_update, t_error, t_start
import pandas as pd
import datetime
import errno
import json
import os
import uuid

class Jobs():
    __storage_sem = None
    __path_user_files = None
    __logger = None
    __naas_folder = '.naas'
    __json_name = 'jobs.json'

    def __init__(self, logger, clean = False, init_data = []):
        self.__path_user_files = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
        self.__path_naas_files = os.path.join(self.__path_user_files, self.__naas_folder)
        self.__json_secrets_path = os.path.join(self.__path_naas_files, self.__json_name)
        # self.__storage_sem = BoundedSemaphore(1)
        self.__storage_sem = Semaphore(1)
        self.__logger = logger
        if not os.path.exists(self.__path_naas_files):
            try:
                print('Init Naas folder Jobs')
                os.makedirs(self.__path_naas_files)
            except OSError as exc: # Guard against race condition
                print('__path_naas_files', self.__path_naas_files)
                if exc.errno != errno.EEXIST:
                    raise 
            except Exception as e:
                print('Exception', e)
        if not os.path.exists(self.__json_secrets_path) or clean:
            uid = str(uuid.uuid4())
            try:
                print('Init Job Storage', self.__json_secrets_path)
                self.__save(uid, init_data)
            except Exception as e:
                print('Exception', e)
                self.__logger.error(
                    {'id': uid, 'type': 'init_job_storage', "status": 'error', 'error': str(e)})          

    def __save(self, uid, data):
        try:
            with open(self.__json_secrets_path, 'w+') as f:
                f.write(json.dumps(data, sort_keys=True, indent=4).replace('NaN' , 'null'))
                f.close()
        except Exception as err:
            print('__save Exception', err)
            self.__logger.error({'id': str(uid), 'type': 'set_job_storage',
                                    "status": 'exception', 'filepath': self.__json_secrets_path, 'error': str(err)})

    def find_by_value(self, uid, value, target_type):
        data = self.list(uid)
        if (len(data) > 0):
            job_list = pd.DataFrame(data)
            cur_jobs = job_list[(job_list.type == target_type)
                            & (job_list.value == value)]
            cur_job = cur_jobs.to_dict('records')
            if (len(cur_job) == 1):
                return cur_job[0]
        return None

    def find_by_path(self, uid, filepath, target_type):
        data = self.list(uid)
        if (len(data) > 0):
            job_list = pd.DataFrame(data)
            cur_jobs = job_list[(job_list.type == target_type)
                            & (job_list.path == filepath)]
            cur_job = cur_jobs.to_dict('records')
            if (len(cur_job) == 1):
                return cur_job[0]
        return None

    def is_running(self, uid, notebook_filepath, target_type):
        cur_job = self.find_by_path(uid, notebook_filepath, target_type)
        if cur_job:
            status = cur_job.get('status', None)
            if (status and status == t_start):
                return True
        return False

    def list(self, uid):
        data = []
        try:
            with open(self.__json_secrets_path, 'r') as f:
                data = json.load(f)
                f.close()
        except Exception as err:
            print('cannot open')
            self.__logger.error({'id': uid, 'type': 'get_job_storage',
                                    "status": 'exception', 'filepath': self.__json_secrets_path, 'error': str(err)})
            data = []
        return data
    
    async def update(self, uid, path, target_type, value, params, status, runTime = 0):
        await self.__storage_sem.acquire()
        data = None
        res = t_error
        try:
            if (len(self.list(uid)) != 0):
                df = pd.DataFrame(self.list(uid))
            else:
                df = pd.DataFrame(columns=['id', 'type', 'value', 'path', 'status', 'params', 'lastUpdate', 'lastRun', 'totalRun']) 
            res = status
            cur_elem = df[(df.type == target_type) & (df.path == path)]
            now = datetime.datetime.now()
            dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
            if (len(cur_elem) == 1):
                if (status == t_delete):
                    self.__logger.info({'id': uid, 'type': target_type, 'value': value, 'status': t_delete,
                                'path': path, 'params': params})
                    df = df.drop(cur_elem.index)
                else:
                    self.__logger.info({'id': uid, 'type': target_type, 'value': value, 'status': t_update,
                            'path': path, 'params': params})
                    index = cur_elem.index[0]
                    df.at[index,'id'] = uid
                    df.at[index,'status'] = status
                    df.at[index,'value'] = value
                    df.at[index,'params'] = params
                    df.at[index,'lastUpdate'] = dt_string
                    if runTime > 0 and status != t_add:
                        df.at[index,'lastRun'] = runTime
                        df.at[index,'totalRun'] = runTime + (df.at[index,'totalRun'] if df.at[index,'totalRun'] else 0)
                    elif status == t_add:
                        df.at[index,'lastRun'] = 0
                        df.at[index,'totalRun'] = 0                    
                    res = t_update
            elif (status == t_add and len(cur_elem) == 0):
                self.__logger.info({'id': uid, 'type': target_type, 'value': value, 'status': t_update,
                        'path': path, 'params': params})
                new_row = [{'id': uid,'type': target_type, 'value': value, 'status': t_add,
                            'path': path, 'params': params, 'lastRun': runTime, 'totalRun': runTime, 'lastUpdate':  dt_string}]
                df_new = pd.DataFrame(new_row)
                df = pd.concat([df, df_new], axis=0)
            else:
                res = t_skip
            data = df.to_dict('records')
            if (res != t_skip):
                self.__save(uid, data)
        except Exception as e:
            print('cannot update', e)
            self.__logger.error({'id': uid, 'type': target_type, 'value': value, 'status': t_error,
                        'path': path, 'params': params, 'error': str(e)})
        self.__storage_sem.release()
        return {"status": res, "data": data}


