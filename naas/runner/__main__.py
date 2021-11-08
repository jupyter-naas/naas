from .runner import Runner
import argparse
import os


def createProductionSymlink():
    # Create Production symlink.
    try:
        os.makedirs("/home/ftp/.naas/home/ftp", exist_ok=True)
        os.symlink("/home/ftp/.naas/home/ftp", "/home/ftp/⚡ → Production")
    except FileExistsError as e:
        print(e)
        pass
    except:  # noqa: E722
        print("An error occured while creating production symlink.")
        pass


if __name__ == "__main__":
    createProductionSymlink()
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=5000, help="port of the server")
    parser.add_argument("--prod", action="store_true", help="remove debug logs")
    parser.add_argument(
        "-c", "--check", action="store_true", help="check if already running"
    )
    parser.add_argument("-k", "--kill", action="store_true", help="kill me")
    args = parser.parse_args()
    port = int(args.port) if args.port else None
    kill = True if args.kill else False
    debug = False if args.prod else True
    runner = Runner()
    if kill:
        runner.kill()
    else:
        runner.start(port=port, debug=debug)
