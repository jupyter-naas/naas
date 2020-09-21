# Copyright (c) Naas Team.
# Distributed under the terms of the Modified BSD License.

from .refresh import Refresh
from .api import Api
from .static import Static
from .dependency import Dependency
from IPython.core.display import display, HTML
from .secret import Secret
from .runner import Runner
from .runner.proxy import encode_proxy_url
import requests
import json
import os

''' Naas code '''

__location__ = os.getcwd()
refresh = Refresh
secret = Secret
runner = Runner
api = Api
static = Static
dependency = Dependency

def version():
    try:
        with open(os.path.join(__location__, 'info.json'), 'r') as json_file:
            version = json.load(json_file)
            return version
    except:
        return {'error': 'version error'}

def manager():
    public_url = f'{encode_proxy_url()}/manager'
    print('You can check your current tasks list here :')
    display(HTML(f'<a href="{public_url}"">Manager</a>'))

def refresh_status():
    req = requests.get(url='localhost:5000/scheduler')
    req.raise_for_status()
    jsn = req.json()
    print(jsn) 
    return jsn

def refresh_pause():
    req = requests.get(url='localhost:5000/scheduler/pause')
    req.raise_for_status()
    jsn = req.json()
    print(jsn) 
    return jsn
    
def refresh_resume():
    req = requests.get(url='localhost:5000/scheduler/resume')
    req.raise_for_status()
    jsn = req.json()
    print(jsn) 
    return jsn

__version__ = f"Nass {version()}"

def welcome():
    print('[Nass from JupyterHub] => Welcome to your ETL, read the documentation')
    print('Do naas.help() to get more info on what you can do.\n')

def help():
    print('naas.version() => Get the current version\n')
    print('naas.manager() => Get the url of the manager\n')
    print('naas.refresh => Get the notebook refresh driver\n')
    print('naas.api => Get the notebook api driver\n')
    print('naas.static => Get the file sharing driver\n')
    print('naas.dependency => Get the file dependency driver\n')
