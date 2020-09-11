from .types import t_delete, t_add, t_skip, t_edited, t_error, t_static, t_notebook, t_scheduler, t_dependency
from IPython.core.display import display, JSON, Image, HTML, SVG, Markdown
from distutils.dir_util import copy_tree
from notebook import notebookapp
from .proxy import get_proxy_url
from shutil import copy2
import pretty_cron
import ipykernel
import traceback
import requests
import datetime
import urllib
import errno
import json
import os
import re

__port = os.environ.get('naas_RUNNER_PORT', 5000)

local_api = f'http://localhost:{__port}'

def notebook_path():
    """Returns the absolute path of the Notebook or None if it cannot be determined
    NOTE: works only when the security is token-based or there is also no password
    """
    try:
        connection_file = os.path.basename(ipykernel.get_connection_file())
        kernel_id = connection_file.split('-', 1)[1].split('.')[0]

        for srv in notebookapp.list_running_servers():
            try:
                base_url = f'{os.environ["PUBLIC_DATASCIENCE"]}/user/{os.environ["JUPYTERHUB_USER"]}/api/sessions'
                req = urllib.request.urlopen(f'{base_url}?token='+os.environ['JUPYTERHUB_API_TOKEN'])
                sessions = json.load(req)
                for sess in sessions:
                    if sess['kernel']['id'] == kernel_id:
                        return os.path.join(srv['notebook_dir'],sess['notebook']['path'])
            except:
                pass  # There may be stale entries in the runtime directory 
    except:
        pass
    return None

def get_path(path):
    if path is not None:
        return os.path.abspath(os.path.join(os.getcwd(), path))
    else:
        return notebook_path()
    
class FileManager():
    base_ftp_path = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
    production_path = None
    folder_name = '.naas'
    json_files = 'tasks.json'
    readme_name = 'README.md'
    json_files_path = None
    readme_path = None

    def __init__(self, production_path=None, json_files=None):
        self.production_path = os.path.join(self.base_ftp_path, self.folder_name)
        if production_path is not None:
            self.production_path = production_path
        if json_files is not None:
            self.json_files = json_files
        self.json_files_path = os.path.join(self.production_path, self.json_files)
        self.readme_path = os.path.join(self.production_path, self.readme_name)
        if not os.path.exists(os.path.dirname(self.json_files_path)):
            try:
                os.makedirs(os.path.dirname(self.json_files_path))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        try:
            with open(self.readme_path, 'w+') as readme:
                readme.write('Welcome NAAS')
                readme.close()
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise 

    def public_url(self, token, endpoint=None):
        public_url = get_proxy_url(token)
        if endpoint:
            public_url = f"{public_url}/{endpoint}"
        return public_url

    def get_prod_path(self, path):
        new_path = path.replace(self.base_ftp_path, self.production_path)
        return new_path

    def __copy_file_in_dev(self, path, replace=False):
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

    def __del_copy_file_in_prod(self, path):
        if path.find(self.production_path) == -1:
            raise Exception(f"Cannot delte file {path} it's in other folder than {self.production_path}")
        if os.path.exists(path):
            os.remove(path)

    def get_naas(self):
        naas_data = []
        try:
            with open(self.json_files_path, 'r') as f:
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

    def updateTask(self, obj, mode, silent):
        json_data = self.get_naas()
        new_task = []
        replaced = False
        for item in json_data:
            if obj['path'] == item['path'] and obj['type'] == item['type']:
                if mode == 'add':
                    new_task.append(obj)
                    if silent is False:
                        print('Edited =>>', obj)
                else:
                    print('Deleted =>>', obj)
                replaced = True
            else:
                new_task.append(item)
        if replaced is False:
            if mode == 'add':
                new_task.append(obj)
                if silent is False:
                    print('Added =>>', obj)
            else:
                print('Deleted not found =>>', obj)
        return new_task

    def add_prod(self, obj, silent):
        dev_path = obj.get('path')
        obj['path'] = self.get_prod_path(obj.get('path'))
        if "type" in obj and "path" in obj and "params" in obj and "value" in obj:
            self.__copy_file_in_prod(dev_path)
            r = requests.post(f"{local_api}/v1/tasks", json={**obj, **{'status': t_add}})
            if not silent:
                print(f'{r.json()["status"]} ==> {obj}')
            return obj
        else:
            raise Exception('obj should have all keys ("type","path","params","value" )')

    def del_prod(self, obj, silent):
        obj['path'] = self.get_prod_path(obj.get('path'))
        if "type" in obj and "path" in obj:
            r = requests.post(f"{local_api}/v1/tasks", json={**obj, **{'status': t_delete}})
            if not silent:
                print(f'{r.json()["status"]} ==> {obj}')
            return obj
        else:
            raise Exception('obj should have keys ("type","path")')
        
class Refresh():
    naas = None
    role = t_scheduler

    def __init__(self):
        self.file_manager = FileManager()

    def current_raw(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            if item['type'] == self.role:
                print(item)
    
    def currents(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            kind = None
            if item['type'] == self.role:
                cron_string = pretty_cron.prettify_cron(item['value'])
                kind = f"refresh {cron_string}"
                print(f"File ==> {item['path']} is {kind}")

    def add(self, path=None, reccurence=None, params=None, silent=False):
        if not notebook_path():
            print(
                f'No add done you are in already in naas folder\n')
            return
        if not reccurence:
            print(
                f'No reccurence provided\n')
            return
        cron_string = pretty_cron.prettify_cron(reccurence)
        current_file = get_path(path)
        prod_path = self.file_manager.get_prod_path(current_file)
        if silent is False:
            print(
                f'[Naas from Jupyter] => i have copied this {current_file} here: {prod_path} \n')
            print(f'it will refresh it {cron_string}\n')
            print(
                f'If you want to remove the refresh capability, just call .delete({path if path is not None else "" })) in this file')
        return self.file_manager.add_prod({"type": self.role, "path": current_file, "params": {}, "value": reccurence}, silent)

    def get(self, path=None):
        current_file = get_path(path)
        self.file_manager.get_prod(current_file)
    
    def clear_output(self, path=None):
        current_file = get_path(path)
        self.file_manager.clear_output(current_file)
        
    def get_output(self, path=None):
        current_file = get_path(path)
        self.file_manager.get_output(current_file)

    def get_history(self, path=None, histo=None):
        if not histo:
            print(
                f'No histo provided\n')
            return     
        current_file = get_path(path)
        self.file_manager.get_history(current_file, histo)

    def list_history(self, path=None):
        current_file = get_path(path)
        self.file_manager.list_history(current_file)
        
    def clear_history(self, path=None, histo=None):
        current_file = get_path(path)
        self.file_manager.clear_history(current_file, histo)
        
    def delete(self, path=None, all=False, silent=False):
        if not notebook_path():
            print(
                f'No delete done you are in already in naas folder\n')
            return
        current_file = get_path(path)
        self.file_manager.del_prod({"type": self.role, "path": current_file}, silent)
        if all is True:
            self.file_manager.clear_history(current_file)
            self.file_manager.clear_output(current_file) 
    
    def help(self):
        print(f'=== {type(self).__name__} === \n')
        print(f'.add(path, params) => add path to the prod {type(self).__name__} server\n')
        print(f'.delete(path) => delete path to the prod {type(self).__name__} server\n')
        print('.clear_history(histonumber, path) => clear history, history number and path are optionel, if you don\'t provide them it will erase full history of current file \n')
        print('.list_history(path) => list history, of a path or if not provided the current file \n')
        print('.get_history(histonumber, path) => get history file, of a path or if not provided the current file \n')
        print('.get(path) => get current prod file of a path, or if not provided the current file \n')
        print(f'.currents() => get current list of {type(self).__name__} prod file\n')
        print(f'.current_raw() => get json current list of {type(self).__name__} prod file\n')
        
class Api():
    naas = None
    role = t_notebook

    def __init__(self):
        self.file_manager = FileManager()

    def current_raw(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            if item['type'] == self.role:
                print(item)
    
    def currents(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            kind = None
            if item['type'] == self.role:
                kind = f"callable with this url {self.file_manager.public_url(item['value'], 'start')} from anywhere"
                print(f"File ==> {item['path']} is {kind}")

    def add(self, path=None, params={}, silent=False):
        current_file = get_path(path)
        if current_file is None:
            print('Missing file path in prod mode')
            return
        prod_path = self.file_manager.get_prod_path(current_file)
        token = self.file_manager.get_value(prod_path, self.role)
        if token is None:
            token = os.urandom(30).hex()
        url = self.file_manager.public_url(token, 'start')
        if not notebook_path():
            print(
                f'No add done you are in already in naas folder\n')
            return url
        if silent is False:
            print(
                f'[Naas from Jupyter] => i have copied this {current_file} here: {prod_path} \n')
            print(
                f'You can now use it in Naas workspace with this url : {url} \n')
            display(HTML(f'<a href="{url}"">{url}</a>'))
            print(
                f'If you want to remove the api capability, just call .delete({path if path is not None else "" })) in this file')
        self.file_manager.add_prod({"type": self.role, "path": current_file, "params": params, "value": token}, silent)
        return url

    def respond_html(self, data):
        display(HTML(data, metadata={'naas_api': True}))

    def respond_json(self, data):        
        display(JSON(data, metadata={'naas_api': True}))

    def respond_image(self, data, filename, mimetype):
        display(Image(data, filename=filename, format=mimetype, metadata={'naas_api': True}))
        
    def respond_svg(self, data):
        display(SVG(data, metadata={'naas_api': True}))
        
    def respond_markdown(self, data):
        display(Markdown(data, metadata={'naas_api': True}))
                                
    def get(self, path=None):
        current_file = get_path(path)
        self.file_manager.get_prod(current_file)

    def get_output(self, path=None):
        current_file = get_path(path)
        self.file_manager.get_output(current_file)

    def clear_output(self, path=None):
        current_file = get_path(path)
        self.file_manager.clear_output(current_file)
                
    def get_history(self, path=None, histo=None):
        if not histo:
            print(
                f'No histo provided\n')
            return     
        current_file = get_path(path)
        self.file_manager.get_history(current_file, histo)

    def list_history(self, path=None):
        current_file = get_path(path)
        self.file_manager.list_history(current_file)
        
    def clear_history(self,  path=None, histo=None):
        current_file = get_path(path)
        self.file_manager.clear_history(current_file, histo)

    def delete(self, path=None, all=False, silent=False):
        if not notebook_path():
            print(
                f'No delete done you are in already in naas folder\n')
            return
        current_file = get_path(path)
        self.file_manager.del_prod({"type": self.role, "path": current_file}, silent)
        if all is True:
            self.file_manager.clear_history(current_file)
            self.file_manager.clear_output(current_file) 
                
    def help(self):
        print(f'=== {type(self).__name__} === \n')
        print(f'.add(path, params) => add path to the prod {type(self).__name__} server\n')
        print(f'.delete(path) => delete path to the prod {type(self).__name__} server\n')
        print('.clear_history(path, histonumber) => clear history, history number and path are optionel, if you don\'t provide them it will erase full history of current file \n')
        print('.list_history(path) => list history, of a path or if not provided the current file \n')
        print('.get_history(histonumber, path) => get history file, of a path or if not provided the current file \n')
        print('.get(path) => get current prod file of a path, or if not provided the current file \n')
        print(f'.currents() => get current list of {type(self).__name__} prod file\n')
        print(f'.current_raw() => get json current list of {type(self).__name__} prod file\n')

class Static():
    naas = None
    role = t_static

    def __init__(self):
        self.file_manager = FileManager()

    def current_raw(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            if item['type'] == self.role:
                print(item)
    
    def currents(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            kind = None
            if item['type'] == self.role:
                kind = f"publicly gettable with this url {self.file_manager.public_url(item['value'])}"
                print(f"File ==> {item['path']} is {kind}")

    def get(self, path=None):
        if not notebook_path():
            print(
                f'No get done you are in already in naas folder\n')
            return  
        current_file = get_path(path)
        self.file_manager.get_prod(current_file)

    def get_history(self, histo, path=None):
        if not notebook_path():
            print(
                f'No get history done you are in already in naas folder\n')
            return  
        current_file = get_path(path)
        self.file_manager.get_history(current_file, histo)

    def list_history(self, path=None):
        current_file = get_path(path)
        self.file_manager.list_history(current_file)
        
    def clear_history(self, path=None, histo=None):
        if not notebook_path():
            print(
                f'No clear history done you are in already in naas folder\n')
            return  
        current_file = get_path(path)
        self.file_manager.clear_history(current_file, histo)
                
    def add(self, path=None, params={}, silent=False, Force=False):
        current_file = get_path(path)
        if current_file is None:
            print('Missing file path in prod mode')
            return
        prod_path = self.file_manager.get_prod_path(current_file)
        token = self.file_manager.get_value(prod_path, self.role)
        if token is None or Force is True:
            token = os.urandom(30).hex()
        url = self.file_manager.public_url(token)
        if not notebook_path() and Force is False:
            print(
                f'No add done you are in already in naas folder\n')
            return url
        if silent is False:
            print(
                f'[Naas from Jupyter] => i have copied this {current_file} here: {prod_path} \n')
            print(
                f'You can now call from anywere this url : \n')
            display(HTML(f'<a href="{url}"">{url}</a>'))
            print(
                f'If you want to remove the api capability, just call .delete({path if path is not None else "" }) in this file')
        self.file_manager.add_prod({"type": self.role, "path": current_file, "params": params, "value": token}, silent)
        return url

    def delete(self, path=None, all=False, silent=False):
        if not notebook_path():
            print(
                f'No delete done you are in already in naas folder\n')
            return        
        current_file = get_path(path)
        self.file_manager.del_prod({"type": self.role, "path": current_file}, silent)
        if all is True:
            self.file_manager.clear_history(current_file)
            self.file_manager.clear_output(current_file) 
            
    def help(self):
        print(f'=== {type(self).__name__} === \n')
        print(f'.add(path, params) => add path to the prod {type(self).__name__} server\n')
        print(f'.delete(path) => delete path to the prod {type(self).__name__} server\n')
        print('.clear_history(path, histonumber) => clear history, history number and path are optionel, if you don\'t provide them it will erase full history of current file \n')
        print('.list_history(path) => list history, of a path or if not provided the current file \n')
        print('.get_history(path, histonumber) => get history file, of a path or if not provided the current file \n')
        print('.get(path) => get current prod file of a path, or if not provided the current file \n')
        print(f'.currents() => get current list of {type(self).__name__} prod file\n')
        print(f'.current_raw() => get json current list of {type(self).__name__} prod file\n')
        
class Dependency():
    naas = None
    role = t_dependency

    def __init__(self):
        self.file_manager = FileManager()

    def current_raw(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            if item['type'] == self.role:
                print(item)
    
    def currents(self):
        json_data = self.file_manager.get_naas()
        for item in json_data:
            if item['type'] == self.role:
                print(f"File ==> {item['path']}")

    def get(self, path=None):
        if not notebook_path():
            print(
                f'No get done you are in already in naas folder\n')
            return  
        current_file = get_path(path)
        self.file_manager.get_prod(current_file)

    def get_history(self, histo, path=None):
        if not notebook_path():
            print(
                f'No get history done you are in already in naas folder\n')
            return  
        current_file = get_path(path)
        self.file_manager.get_history(current_file, histo)

    def list_history(self, path=None):
        current_file = get_path(path)
        self.file_manager.list_history(current_file)
        
    def clear_history(self, path=None, histo=None):
        if not notebook_path():
            print(
                f'No clear history done you are in already in naas folder\n')
            return  
        current_file = get_path(path)
        self.file_manager.clear_history(current_file, histo)
                
    def add(self, path=None, silent=False):
        if not notebook_path():
            print(
                f'No add done you are in already in naas folder\n')
            return
        current_file = get_path(path)
        prod_path = self.file_manager.get_prod_path(current_file)
        if silent is False:
            print(
                f'[Naas from Jupyter] => i have copied this {current_file} here: {prod_path} \n')
            print(
                f'If you want to remove the {type(self).__name__} capability, just call Naas.input.delete() in this file')
        return self.file_manager.add_prod({"type": self.role, "path": current_file, "params": {}, "value": 'Only internal'}, silent)

    def delete(self, path=None, all=False, silent=False):
        if not notebook_path():
            print(
                f'No delete done you are in already in naas folder\n')
            return        
        current_file = get_path(path)
        self.file_manager.del_prod({"type": self.role, "path": current_file}, silent)
        if all is True:
            self.file_manager.clear_history(current_file)
            self.file_manager.clear_output(current_file) 
            
    def help(self):
        print(f'=== {type(self).__name__} === \n')
        print('.add(path) => add path to the prod server\n')
        print(f'.delete(path) => delete path to the prod {type(self).__name__} server\n')
        print('.clear_history(path, histonumber) => clear history, history number and path are optionel, if you don\'t provide them it will erase full history of current file \n')
        print('.list_history(path) => list history, of a path or if not provided the current file \n')
        print('.get_history(path, histonumber) => get history file, of a path or if not provided the current file \n')
        print('.get(path) => get current prod file of a path, or if not provided the current file \n')
        print(f'.currents() => get current list of {type(self).__name__} prod file\n')
        print(f'.current_raw() => get json current list of {type(self).__name__} prod file\n')