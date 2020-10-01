import pytest  # noqa: F401
import os

user_folder_name = "test_user_folder"

os.environ["JUPYTER_SERVER_ROOT"] = os.path.join(os.getcwd(), user_folder_name)

# TODO find a way to test it
