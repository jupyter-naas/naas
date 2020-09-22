from .runner import Runner
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=5000, help="port of the server")
    parser.add_argument("--prod", action="store_true", help="remove debug logs")
    parser.add_argument(
        "-c", "--check", action="store_true", help="check if already running"
    )
    parser.add_argument("-d", "--deamon", action="store_true", help="deamon mode")
    parser.add_argument("-k", "--kill", action="store_true", help="kill me")
    args = parser.parse_args()
    port = int(args.port) if args.port else None
    deamon = True if args.deamon else False
    kill = True if args.kill else False
    debug = False if args.prod else True
    runner = Runner()
    if kill:
        runner.kill()
    else:
        runner.start(deamon=deamon, port=port, debug=debug)
