from gevent.lock import BoundedSemaphore
from .types import t_delete, t_add, t_skip, t_edited, t_error
import pandas as pd
import datetime
import errno
import json
import os

class Jobs():
    _storage_sem = None
    __path_user_files = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
    __naas_file = '.nass'
    __json_name = 'tasks.json'
            
    def __init__(self, uid, logger, clean = False, init_data = []):
        self.__path_naas_files = os.path.join(self.__path_user_files, self.__naas_file)
        self.__json_secrets_path = os.path.join(self.__path_naas_files, self.__json_name)
        if not os.path.exists(self.__path_naas_files):
            try:
                os.makedirs(self.__path_naas_files)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        self._storage_sem = BoundedSemaphore(1)
        self._logger = logger
        if not os.path.exists(self.__path_naas_files):
            try:
                os.makedirs(self.__path_naas_files)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise        
        if not os.path.exists(self.__json_secrets_path) or clean:
            try:
                print('Init Job Storage')
                self.save(uid, init_data)
            except Exception as e:
                self._logger.error(json.dumps(
                    {'id': uid, 'type': 'init_job_storage', "status": 'error', 'error': str(e)}))            

    def find_by_value(self, uid, value, target_type):
        job_list = pd.DataFrame(self.get(uid))
        cur_job = job_list[(job_list.type == target_type)
                        & (job_list.value == value)]
        return cur_job


    def find_by_path(self, uid, filepath, target_type):
        job_list = pd.DataFrame(self.get(uid))
        cur_job = job_list[(job_list.type == target_type)
                        & (job_list.path == filepath)]
        return cur_job
              
    def get(self, uid):
        data = []
        try:
            with open(self.__json_secrets_path, 'r') as f:
                data = json.load(f)
                f.close()
        except Exception as err:
            self._logger.error(json.dumps({'id': uid, 'type': 'get_job_storage',
                                    "status": 'exception', 'filepath': self.__json_secrets_path, 'error': str(err)}))
            data = []
        return data
    
    def save(self, uid, data):
        try:
            with open(self.__json_secrets_path, 'w') as f:
                f.write(json.dumps(data, sort_keys=True, indent=4).replace('NaN' , 'null'))
                f.close()
        except Exception as err:
            self._logger.error(json.dumps({'id': str(uid), 'type': 'set_job_storage',
                                    "status": 'exception', 'filepath': self.__json_secrets_path, 'error': str(err)}))

    def update(self, path, target_type, value, params, status, uid, runTime = 0):
        self._storage_sem.acquire(timeout=10)
        try:
            df = pd.DataFrame(self.get(uid))
            res = status
            cur_elem = df[(df.type == target_type) & (df.path == path)]
            now = datetime.datetime.now()
            dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
            if (len(cur_elem) == 1):
                if (status == t_delete):
                    self._logger.info(json.dumps({'id': uid, 'type': target_type, 'value': value, 'status': t_delete,
                                'path': path, 'params': params}))
                    df = df.drop(cur_elem.index)
                else:
                    self._logger.info(json.dumps({'id': uid, 'type': target_type, 'value': value, 'status': t_edited,
                            'path': path, 'params': params}))
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
                    res = t_edited
            elif (status == t_add and len(cur_elem) == 0):
                self._logger.info(json.dumps({'id': uid, 'type': target_type, 'value': value, 'status': t_edited,
                        'path': path, 'params': params}))
                new_row = [{'id': uid,'type': target_type, 'value': value, 'status': t_add,
                            'path': path, 'params': params, 'lastRun': runTime, 'totalRun': runTime,' lastUpdate':  dt_string}]
                df_new = pd.DataFrame(new_row)
                df = pd.concat([df, df_new], axis=0)
            else:
                res = t_skip
            data = df.to_dict('records')
            if (res != t_skip):
                self.save(uid, data)
        except Exception as e:
            self._logger.error(json.dumps({'id': uid, 'type': target_type, 'value': value, 'status': t_error,
                        'path': path, 'params': params, 'error': str(e)}))
        self._storage_sem.release()
        return {"status": res, "data": data}


