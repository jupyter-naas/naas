from .runner import Runner  # noqa: F401
from naas.runner.env_var import n_env  # noqa: F401


def remote_connect(user, token):
    n_env.token = token
    n_env.user = user
