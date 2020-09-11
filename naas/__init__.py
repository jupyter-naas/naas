from .file_manager import Refresh, Api, Static, Dependency
from IPython.core.display import display, HTML
from .secret import Secret
from .runner import Secret
from .proxy import get_proxy_url
import system
import requests
import json
import os

''' Naas code '''

__location__ = os.getcwd()
refresh = Refresh
secret = Secret
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
    public_url = get_proxy_url('manager')
    print('You can check your current tasks list here :')
    display(HTML(f'<a href="{public_url}"">Manager</a>'))

def brain_restart():
    system(f"python {os.path.join(__location__, 'runner.py')}")
    print('Brain restarted')

def refresh_status():
    req = requests.get(url='localhost:5000/v1/scheduler/status')
    req.raise_for_status()
    jsn = req.json()
    print(jsn) 
    return jsn

def refresh_pause():
    req = requests.get(url='localhost:5000/v1/scheduler/pause')
    req.raise_for_status()
    jsn = req.json()
    print(jsn) 
    return jsn
    
def refresh_resume():
    req = requests.get(url='localhost:5000/v1/scheduler/resume')
    req.raise_for_status()
    jsn = req.json()
    print(jsn) 
    return jsn
    
def brain_reset():
    system('rm -rf /home/ftp/ftp/.brain')
    system('cp -r /home/secret/.brain/*.json /home/ftp/ftp/.brain')
    system('cp -r /home/secret/.brain/*.csv /home/ftp/ftp/.brain')
    print('Brain reset')
    
def manager_logs():
    system('cp /home/ftp/ftp/.brain/logs.csv /home/ftp/ftp/logs.csv')
    
def noop():
    print('In production, this function replace the original function called from bob.static, bob.refresh or bob.api in your notebook.\n')

def singleuser_version():
    try:
        with open(os.path.join('/home/secret', 'info.json'), 'r') as json_file:
            version = json.load(json_file)
            return version
    except:
        return 'version error'

__version__ = f"Brain {version()} \n\nSingle user {singleuser_version()}"

def welcome():
    print('[Bob from JupyterHub] => Welcome to your financial data pipeline, read the documentation')
    print('Do bob.help() to get more info on what you can do.\n')

def help():
    print('=== Internals === \n')
    print('bob.version() => Get the current version\n')
    
    print('=== Manager === \n')
    print('bob.manager() => Get the url of the manager\n')
    print('bob.refresh => Get the notebook refresh driver\n')
    print('bob.api => Get the notebook api driver\n')
    print('bob.static => Get the file sharing driver\n')
    print('bob.dependency => Get the file dependency driver\n')
    
    print('=== Drivers who need init === \n')
    print('bob.darkknight() => Init the driver to connect to our backend \n')
    print('bob.ftp() => Init the driver to connect to ftp\n')
    print('bob.ftps() => Init the driver to connect to ftps\n')
    print('bob.git() => Init the driver to connect to git\n')
    print('bob.healthcheck() => Init the driver to connect to healthcheck\n')
    print('bob.google_spreadsheet() => Init the driver to connect to GoogleSpreadsheet\n')
    print('bob.mailer() => Init the driver to send email\n')

    print('=== Drivers simple === \n')
    print('bob.mongo => Get the Mongo driver\n')
    print('bob.pdf => Get the pdf generator driver\n')
    print('bob.sentiment => Get the sentiment driver\n')
    print('bob.ml => Get the machine learning driver\n')
    print('bob.geo => Get the GeoLocator driver\n')
    print('bob.plot => Get the plot driver\n')
    print('bob.pdf => Get the pdf driver\n')

