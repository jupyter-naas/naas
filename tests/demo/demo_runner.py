from .runner import Runner
import os

path_srv_root = os.path.join(os.getcwd(), "test")

runner = Runner(
    path=path_srv_root,
    port=5000,
    user="joyvan@gmail.com",
    public="localhost:5000",
    proxy="proxy:5000",
)
runner.start()
