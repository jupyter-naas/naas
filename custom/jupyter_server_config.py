# Copyright (c) Naas Team.
# Distributed under the terms of the Modified BSD License.

import subprocess
import os
import logging
import threading
import time

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


runner = threading.Thread(target=naasRunner, args=(naas_port,))
runner.start()

starter = threading.Thread(target=naasStarter, args=())
starter.start()

templates = threading.Thread(target=naasTemplates, args=())
templates.start()
