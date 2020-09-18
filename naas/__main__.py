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
    runner = Runner(port=args.port)
    runner.start(deamon=False)