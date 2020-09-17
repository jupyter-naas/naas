import argparse
from .runner import Runner
import os

def check_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-P', '--port', action='store_false')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = check_options()
    path = os.environ.get('JUPYTER_SERVER_ROOT', os.getcwd())
    user = os.environ.get('JUPYTERHUB_USER', 'joyvan@gmail.com')
    runner = Runner(path=path, port=args.port, user=user)
    runner.start(deamon=False)