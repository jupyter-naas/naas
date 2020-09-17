import pytest
import os

user_folder_name = 'test_user_folder'

os.environ["JUPYTER_SERVER_ROOT"] = os.path.join(os.getcwd(), user_folder_name)

# def test_init():
    # secret = Secret()
    # assert len(secret.list()) == 0
