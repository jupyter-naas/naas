# Copyright (c) Naas Team.
# Distributed under the terms of the Modified BSD License.

from jupyter_core.paths import jupyter_data_dir
import subprocess
import os
import errno
import stat

c = get_config()
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.default_url = '/lab'

# c.LabBuildApp.minimize = False
# c.LabBuildApp.dev_build = False

c.NotebookApp.webbrowser_open_new = 0

c.NotebookApp.tornado_settings = {
    'headers': {
        'Content-Security-Policy': 'frame-ancestors self ' + os.environ.get('ALLOWED_IFRAME', '')
    }
}

# c.LauncherShortcuts.shortcuts = {
#     'naas_manager': {
#         'title': 'Naas Manager2',
#         'target': '{base_url}naas/',
#         'icon_path': '/etc/naas/naas_logo.svg',
#     }
# }

c.ServerProxy.servers = {
    'naas': {
        'launcher_entry': {
            'enabled': True,
            'icon_path': '/etc/naas/naas_logo.svg',
            'title': 'Naas manager',
        },
        'new_browser_tab': False,
        'timeout': 30,
        'command': ["redir", "--lport={port}", "--cport=5000"],
    }
}

# Generate a self-signed certificate
if 'GEN_CERT' in os.environ:
    dir_name = jupyter_data_dir()
    pem_file = os.path.join(dir_name, 'notebook.pem')
    try:
        os.makedirs(dir_name)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
            pass
        else:
            raise

    # Generate an openssl.cnf file to set the distinguished name
    cnf_file = os.path.join(
        os.getenv('CONDA_DIR', '/usr/lib'), 'ssl', 'openssl.cnf')
    if not os.path.isfile(cnf_file):
        with open(cnf_file, 'w') as fh:
            fh.write('''\
[req]
distinguished_name = req_distinguished_name
[req_distinguished_name]
''')

    # Generate a certificate if one doesn't exist on disk
    subprocess.check_call(['openssl', 'req', '-new',
                           '-newkey', 'rsa:2048',
                           '-days', '365',
                           '-nodes', '-x509',
                           '-subj', '/C=XX/ST=XX/L=XX/O=generated/CN=generated',
                           '-keyout', pem_file,
                           '-out', pem_file])
    # Restrict access to the file
    os.chmod(pem_file, stat.S_IRUSR | stat.S_IWUSR)
    c.NotebookApp.certfile = pem_file

# Change default umask for all subprocesses of the notebook server if set in
# the environment
if 'NB_UMASK' in os.environ:
    os.umask(int(os.environ['NB_UMASK'], 8))

os.system('python -m naas.runner &')
