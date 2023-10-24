# Copyright (c) Naas Team.
# Distributed under the terms of the Modified BSD License.

import subprocess
import os
import logging
import threading
import time
from glob import glob

c = get_config()
c.ServerApp.ip = "0.0.0.0"
c.ServerApp.port = 8888

naas_port = 5000

c.ServerApp.open_browser = False
c.ServerApp.webbrowser_open_new = 0

c.ServerApp.tornado_settings = {
    "headers": {
        "Content-Security-Policy": "frame-ancestors self "
        + os.environ.get("ALLOWED_IFRAME", "")
    }
}

c.ServerProxy.servers = {
    "naas": {
        "launcher_entry": {
            "enabled": False,
            "icon_path": "/etc/naas/custom/naas_fav.svg",
            "title": "Naas Lab Manager",
        },
        "new_browser_tab": False,
        "timeout": 30,
        "command": ["redir", ":{port}", f":{naas_port}"],
    }
}

# Change default umask for all subprocesses of the notebook server if set in
# the environment
if "NB_UMASK" in os.environ:
    os.umask(int(os.environ["NB_UMASK"], 8))


def naasRunner(naas_port):
    while True:
        logging.info("Starting naas runner on port {}.".format(naas_port))
        p = subprocess.Popen(["python", "-m", "naas.runner", "-p", f"{naas_port}"])
        p.wait()
        logging.info("Naas Runner exited !")
        logging.info(p.stdout)
        logging.info(p.stderr)
        time.sleep(1)


ONE_HOUR: float = 3600.0


def naasStarter():
    while True:
        logging.info("Refreshing naas starter")
        folder_name = "__tutorials__"

        # Change this to remove a folder from the home directory of the user.
        os.system('rm -rf "/home/ftp/⚡ Get started with Naas"')

        os.system(
            "git clone https://github.com/jupyter-naas/starters.git /home/ftp/.naas/starters|| (cd /home/ftp/.naas/starters && git reset --hard && git pull)"
        )
        os.system(f'mkdir -p "/home/ftp/{folder_name}"')
        os.system(
            f'cp -r /home/ftp/.naas/starters/* "/home/ftp/{folder_name}" && rm "/home/ftp/{folder_name}/README.md"'
        )
        os.system("rm /home/ftp/Welcome_to_Naas.ipynb")
        time.sleep(ONE_HOUR)



def naasTemplates():
    while True:
        logging.info("Refreshing templates")
        folder_name = "__templates__"

        # Change this to remove a folder from the home directory of the user.
        # os.system('rm -rf /home/ftp/')

        os.system(
            "git clone https://github.com/jupyter-naas/awesome-notebooks.git /home/ftp/.naas/awesome-notebooks|| (cd /home/ftp/.naas/awesome-notebooks && git reset --hard && git pull)"
        )
        os.system(f'mkdir -p "/home/ftp/{folder_name}"')
        os.system(
            f'cp -r /home/ftp/.naas/awesome-notebooks/* "/home/ftp/{folder_name}" && rm "/home/ftp/{folder_name}/README.md"'
        )
        time.sleep(ONE_HOUR)

def get_current_commit(dir_path):
    commit_hash = None
    try:
        # Run the Git command to get the current commit hash
        commit_hash = subprocess.check_output(['git', '-C', dir_path, 'rev-parse', 'HEAD']).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Failed to get current commit: {e}")
    
    return commit_hash

def store_last_installed_version(dir_path, version, install_log_file='.last_installed_version'):
    installed_version_file = os.path.join(dir_path, install_log_file)
    with open(installed_version_file, 'w') as f:
        f.write(version)
    return installed_version_file
        
def get_last_installed_version(dir_path, install_log_file='.last_installed_version'):
    last_installed_version = None
    installed_version_file = os.path.join(dir_path, install_log_file)
    if os.path.exists(installed_version_file):
        with open(installed_version_file, 'r') as f:
            last_installed_version = f.read()
    return last_installed_version

def naasABIInstaller():
    while True:
        try:
            logging.info("Refreshing ABI setup")

            config = [
                {
                    'repository': 'https://github.com/jupyter-naas/abi.git',
                    'target': '/home/ftp/__abi__',
                    'version': 'main'
                }
            ]

            for c in config:
                # Clone repository
                os.system(
                    f"git clone {c['repository']} {c['target']}"
                )
                
                # Get last installed version
                last_installed_version = get_last_installed_version(c['target'])
                print(last_installed_version)

                # Reset hard and pull latest version.
                os.system(
                    f"cd {c['target']} && git reset --hard && git checkout {c['version']} && git pull"
                )
                
                # Grab current commit version
                current_commmit = get_current_commit(c['target'])
                print(current_commmit)
                
                # Check if current commit is different than last installed version.
                # If yes then we execute all targeted notebooks.
                if current_commmit != last_installed_version:
                    
                    os.system(
                        f"cd {c['target']} && pip install --user -r requirements.txt"
                    )
                    
                    entrypoints = glob(os.path.join(c['target'], '**', '__plugin__.ipynb'), recursive=True)
                    for entrypoint in entrypoints:
                        working_directory = '/'.join(entrypoint.split('/')[:-1])

                        execute_cmd = f"cd {working_directory} && papermill {entrypoint.split('/')[-1]} {entrypoint.split('/')[-1]}.setup-execution.ipynb" 

                        os.system(
                            execute_cmd
                        )
                    store_last_installed_version(c['target'], current_commmit)
        except Exception as e:
            logging.error(f'Exception while installing ABI', e)
        FIVE_MINUTES = 300
        time.sleep(FIVE_MINUTES)



runner = threading.Thread(target=naasRunner, args=(naas_port,))
runner.start()

starter = threading.Thread(target=naasStarter, args=())
starter.start()

templates = threading.Thread(target=naasTemplates, args=())
templates.start()

abiInstaller = threading.Thread(target=naasABIInstaller, args=())
abiInstaller.start()