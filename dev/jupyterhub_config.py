# Copyright (c) Naas Development Team.
# Distributed under the terms of the Modified BSD License.

# Configuration file for JupyterHub
import os
import requests
from jupyter_client.localinterfaces import public_ips

c = get_config()

# c.NotebookApp.allow_remote_access = True
c.NotebookApp.ResourceUseDisplay.track_cpu_percent = True
c.NotebookApp.ResourceUseDisplay.mem_warning_threshold = 0.1
c.NotebookApp.ResourceUseDisplay.cpu_warning_threshold = 0.1

# We rely on environment variables to configure JupyterHub so that we
# avoid having to rebuild the JupyterHub container every time we change a
# configuration parameter.
c.JupyterHub.template_paths = ["/home/authenticator/naasauthenticator/templates"]
c.JupyterHub.logo_file = "/srv/jupyterhub/naas_fav.svg"
# Spawn single-user servers as Docker containers
c.Spawner.default_url = '/lab'
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'


c.JupyterHub.api_tokens = {
    "secret-token": "service-admin",
}

c.JupyterHub.services = [
    {
        "name": "service-token",
        "admin": True,
        "api_token": os.environ.get('ADMIN_API_TOKEN', 'SHOULD_BE_CHANGED'),
    },
]

# Spawn containers from this image

c.DockerSpawner.image = os.environ['DOCKER_NOTEBOOK_IMAGE']
c.DockerSpawner.pull_policy = 'Always'

# JupyterHub requires a single-user instance of the Notebook server, so we
# default to using the `start-singleuser.sh` script included in the
# jupyter/docker-stacks *-notebook images as the Docker run command when
# spawning containers.  Optionally, you can override the Docker run command
# using the DOCKER_SPAWN_CMD environment variable.


def createEnv(NAAS_GPU=False):
    base_env = {
        'JUPYTERHUB_URL': os.environ.get('JUPYTERHUB_URL', ''),
        'NOTIFICATIONS_API': os.environ.get('NOTIFICATIONS_API', ''),
        'CALLBACK_API': os.environ.get('CALLBACK_API', ''),
        'GSHEETS_API': os.environ.get('GSHEETS_API', ''),
        'CITYFALCON_KEY': os.environ.get('CITYFALCON_KEY', ''),
        'APINEW_KEY': os.environ.get('APINEW_KEY', ''),
        'SCREENSHOT_API': os.environ.get('SCREENSHOT_API', ''),
        'NAAS_SENTRY_DSN': os.environ.get('NAAS_SENTRY_DSN', ''),
        'PROXY_API': os.environ.get('PUBLIC_PROXY_API', ''),
        'ALLOWED_IFRAME': os.environ.get('ALLOWED_IFRAME', ''),
        'JUPYTER_ENABLE_LAB': 'YES',
        'TZ': 'Europe/Paris'
    }
    if NAAS_GPU:
        base_env['NAAS_GPU'] = 'YES'
    return base_env


c.DockerSpawner.environment = createEnv()

# Connect containers to this Docker network
network_name = os.environ['DOCKER_NETWORK_NAME']
# network_name = 'bridge'
c.DockerSpawner.use_internal_ip = True
c.Spawner.mem_limit = '4G'
c.DockerSpawner.network_name = network_name
ip = public_ips()[0]
c.JupyterHub.hub_ip = ip

c.DockerSpawner.extra_host_config = {'network_mode': network_name}

c.DockerSpawner.cmd = ["start-notebook.sh", "--NotebookApp.default_url=lab"]

# Explicitly set notebook directory because we'll be mounting a host volume to
# it.  Most jupyter/docker-stacks *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_dir = os.environ.get('DOCKER_NOTEBOOK_DIR', '/home/joyvan')
c.DockerSpawner.notebook_dir = notebook_dir

c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': {"bind": notebook_dir, "mode": "z"},
}

# Remove containers once they are stopped
c.DockerSpawner.remove_containers = True
# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = True

c.DockerSpawner.start_timeout = 300

# User containers will access hub by container name on the Docker network
c.JupyterHub.hub_port = os.environ.get('PORT', 8081)

c.JupyterHub.hub_ip = 'jupyterhub'
c.JupyterHub.hub_connect_ip = 'jupyterhub'
c.DockerSpawner.hub_connect_ip = 'jupyterhub'

# Authenticate users with GitHub OAuth
c.JupyterHub.authenticator_class = 'naasauthenticator.NaasAuthenticator'
c.Authenticator.check_common_password = True
c.Authenticator.minimum_password_length = 10

# Persist hub data on volume mounted inside container
data_dir = os.environ.get('DATA_VOLUME_CONTAINER', '/data')

c.JupyterHub.cookie_secret_file = os.path.join(data_dir, 'jupyterhub_cookie_secret')

c.JupyterHub.db_url = 'postgresql://postgres:{password}@{host}/{db}'.format(
    host=os.environ['POSTGRES_HOST'],
    password=os.environ['POSTGRES_PASSWORD'],
    db=os.environ['POSTGRES_DB'],
)

c.JupyterHub.tornado_settings = {
    'headers': {
        'Content-Security-Policy': 'frame-ancestors self ' + os.environ.get('ALLOWED_IFRAME', '')
    }
}

# Whitlelist users and admins
c.Authenticator.whitelist = set()
c.Authenticator.admin_users = {"service-admin"}
c.JupyterHub.admin_access = True


def create_user(username, password):
    signup_url = "http://localhost:8000/hub/signup"
    login = {
        "username": username,
        "password": password,
    }
    headers = {"Authorization": f"token {os.environ.get('ADMIN_API_TOKEN')}"}
    try:
        r = requests.post(signup_url, data=login, headers=headers)
        r.raise_for_status()
        print("user created ", username)
    except Exception as e:
        print("cannot create ", username, e)


# create_user('bob@cashstory.com', '1bcbaba339d6f93993c5adf277227a1e')
