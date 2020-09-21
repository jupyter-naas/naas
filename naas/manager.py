from .types import t_delete, t_add, t_skip, t_update, t_error, t_static, t_notebook, t_scheduler, t_dependency
from notebook import notebookapp
from .runner.proxy import encode_proxy_url
from shutil import copy2
import ipykernel
import requests
import datetime
import urllib
import errno
import json
import os
import re

class Manager():
    __port = os.environ.get('NAAS_RUNNER_PORT', 5000)
    __local_api = f'http://localhost:{__port}'
    __base_ftp_path = None
    __public_url = None
    __jup_user = None
    __jup_token = None
    __production_path = None
    __folder_name = '.naas'
    __json_files = 'jobs.json'
    __readme_name = 'README.md'
    __json_files_path = None
    __readme_path = None

    def __init__(self):
        self.__base_ftp_path = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
        self.__public_url = os.environ.get('JUPYTERHUB_URL', '')
        self.__jup_user = os.environ.get('JUPYTERHUB_USER', '')
        self.__jup_token = os.environ.get('JUPYTERHUB_API_TOKEN', '')
        self.__production_path = os.path.join(self.__base_ftp_path, self.__folder_name)
        self.__json_files_path = os.path.join(self.__production_path, self.__json_files)
        self.__readme_path = os.path.join(self.__production_path, self.__readme_name)
        if not os.path.exists(self.__production_path):
            try:
                os.makedirs(self.__production_path)
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        try:
            with open(self.__readme_path, 'w+') as readme:
                readme.write('Welcome NAAS')
                readme.close()
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise 

    def notebook_path(self):
        """Returns the absolute path of the Notebook or None if it cannot be determined
        NOTE: works only when the security is token-based or there is also no password
        """
        try:
            connection_file = os.path.basename(ipykernel.get_connection_file())
            kernel_id = connection_file.split('-', 1)[1].split('.')[0]

            for srv in notebookapp.list_running_servers():
                try:
                    base_url = f'{self.__public_url}/user/{self.__jup_user}/api/sessions'
                    req = urllib.request.urlopen(f'{base_url}?token={self.__jup_token}')
                    sessions = json.load(req)
                    for sess in sessions:
                        if sess['kernel']['id'] == kernel_id:
                            return os.path.join(srv['notebook_dir'],sess['notebook']['path'])
                except:
                    pass  # There may be stale entries in the runtime directory 
        except:
            pass
        return None

    def get_path(self, path):
        if path is not None:
            return os.path.abspath(os.path.join(os.getcwd(), path))
        else:
            return self.notebook_path()

    def proxy_url(self, endpoint, token=None):
        public_url = encode_proxy_url(endpoint)
        if token:
            public_url = f"{public_url}/{endpoint}"
        return public_url

    def get_prod_path(self, path):
        new_path = path.replace(self.__base_ftp_path, self.__production_path)
        return new_path

    def __copy_file_in_dev(self, path):
        new_path = self.get_prod_path(path)
        if not os.path.exists(new_path):
            raise Exception(f"file doesn't exist {new_path}")
        if not os.path.exists(os.path.dirname(path)):
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        dev_dir = os.path.dirname(path)
        dev_finename = os.path.basename(path)
        secure_path = os.path.join(dev_dir, f'prod_{dev_finename}')
        try:
            copy2(new_path, secure_path)
        except Exception as e:
            raise Exception(f"Cannot copied here {secure_path}, file probabily exist {path} {str(e)}")
        print(f'File copied here {secure_path}')
        return secure_path
    
    def __copy_file_in_prod(self, path):
        new_path = self.get_prod_path(path)
        prod_dir = os.path.dirname(new_path)
        prod_finename = os.path.basename(new_path)
        history_filename = f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}_{prod_finename}'
        history_path = os.path.join(prod_dir, history_filename)
        if not os.path.exists(path):
            raise Exception(f"file doesn't exist {path}")
        if not os.path.exists(os.path.dirname(new_path)):
            try:
                os.makedirs(os.path.dirname(new_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        if os.path.exists(new_path):
            os.remove(new_path)
        copy2(path, new_path)
        copy2(path, history_path)
        return new_path

    def __del_file_in_prod(self, path):
        if path.find(self.__production_path) == -1:
            raise Exception(f"Cannot delte file {path} it's in other folder than {self.__production_path}")
        if os.path.exists(path):
            os.remove(path)

    def get_naas(self):
        naas_data = []
        try:
            with open(self.__json_files_path, 'r') as f:
                naas_data = json.load(f)
                f.close()
        except:
            naas_data = [] 
        return naas_data
    
    def get_value(self, path, obj_type):
        json_data = self.get_naas()
        value = None
        for item in json_data:
            if (item['type'] == obj_type and item['path'] == path):
                value = item['value']
        return value

    def is_already_use(self, obj):
        json_data = self.get_naas()
        already_use = False
        for item in json_data:
            if ("type" in obj and "value" in obj
                and ( obj['type'] == t_static or obj['type'] == t_notebook )
                and item['type'] == obj['type']
                and item['value'] == obj['value']):
                already_use = True
        return already_use

    def get_prod(self, path):
        self.__copy_file_in_dev(path)
                
    def get_output(self, path):
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)
        out_path = os.path.join(dirname, f'out_{filename}')
        self.__copy_file_in_dev(out_path)
        
    def clear_output(self, path):
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)
        out_path = os.path.join(dirname, f'out_{filename}')
        print(f'Delete {out_path}')
        os.remove(out_path)   
        
    def list_history(self, path):
        prod_path = self.get_prod_path(path)
        filename = os.path.basename(path)
        dirname = os.path.dirname(prod_path)
        print(f'Avaliable :\n')
        for ffile in os.listdir(dirname):
            if ffile.endswith(filename) and ffile != filename and not ffile.startswith('out'):
                histo = ffile.replace(filename, '')
                histo = histo.replace('_', '')
                print(histo + '\n')
                
    def get_history(self, path, histo):
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)
        path_histo = os.path.join(dirname, f'{histo}_{filename}')
        self.__copy_file_in_dev(path_histo)
                
    def clear_history(self, path, histo=None):
        prod_path = self.get_prod_path(path)
        filename = os.path.basename(path) if not histo else f'{histo}_{os.path.basename(path)}'
        dirname = os.path.dirname(prod_path)
        for ffile in os.listdir(dirname):
            if not ffile.startswith('out_') and ((histo and filename == ffile) or (not histo and ffile.endswith(filename) and filename != ffile)):
                tmp_path = os.path.join(dirname, ffile)
                print(f'Delete {tmp_path}')
                os.remove(tmp_path)    

    def add_prod(self, obj, silent):
        if "type" in obj and "path" in obj and "params" in obj and "value" in obj:
            dev_path = obj.get('path')
            obj['path'] = self.get_prod_path(obj.get('path'))
            self.__copy_file_in_prod(dev_path)
            r = requests.post(f"{self.__local_api}/jobs", json={**obj, **{'status': t_add}})
            if not silent:
                print(f'{r.json()["status"]} ==> {obj}')
            return obj
        else:
            raise Exception('obj should have all keys ("type","path","params","value" )')

    def del_prod(self, obj, silent):
        if "type" in obj and "path" in obj:
            obj['path'] = self.get_prod_path(obj.get('path'))
            self.__del_file_in_prod(obj['path'])
            r = requests.post(f"{self.__local_api}/jobs", json={**obj, **{'status': t_delete}})
            if not silent:
                print(f'{r.json()["status"]} ==> {obj}')
            return obj
        else:
            raise Exception('obj should have keys ("type","path")')
