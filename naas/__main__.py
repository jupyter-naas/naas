import argparse
from .runner import Runner

def check_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-K', '--kill', action='store_false')
    parser.add_argument('-S', '--skip', action='store_false')
    parser.add_argument('-P', '--port', action='store_false')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = check_options()
    runner = Runner(args.skip, args.port)
    if (args.kill):
        runner.kill()
    runner.start()