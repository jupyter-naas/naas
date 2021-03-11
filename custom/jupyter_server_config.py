# Copyright (c) Naas Team.
# Distributed under the terms of the Modified BSD License.

import subprocess
import os

c = get_config()
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888

c.ServerApp.open_browser = False
c.ServerApp.webbrowser_open_new = 0
c.ServerApp.default_url = '/lab'

c.ServerApp.tornado_settings = {
    'headers': {
        'Content-Security-Policy': 'frame-ancestors self ' + os.environ.get('ALLOWED_IFRAME', '')
    }
}

c.ServerProxy.servers = {
    'naas': {
        'launcher_entry': {
            'enabled': True,
            'icon_path': '/etc/naas/naas_fav.svg',
            'title': 'Naas manager',
        },
        'new_browser_tab': False,
        'timeout': 30,
        'command': ["redir", "--lport={port}", "--cport=5000"],
    }
}

# Change default umask for all subprocesses of the notebook server if set in
# the environment
if 'NB_UMASK' in os.environ:
    os.umask(int(os.environ['NB_UMASK'], 8))

subprocess.Popen(['python', '-m', 'naas.runner'])
