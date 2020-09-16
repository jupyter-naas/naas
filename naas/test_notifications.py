import pytest
import os

os.environ["JUPYTER_SERVER_ROOT"] = os.path.join(os.getcwd(), 'test')

# def test_init():
    # secret = Secret()
    # assert len(secret.list()) == 0
