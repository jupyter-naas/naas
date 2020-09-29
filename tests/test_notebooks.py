from naas.types import t_add, t_notebook
from naas.runner.logger import Logger
from naas.runner.notebooks import Notebooks
import getpass
import pytest  # noqa: F401
import uuid
import os
from shutil import copy2

user_folder_name = "test_user_folder"
user = getpass.getuser()


async def test_notebook(test_cli, tmp_path):
    test_notebook = "tests/demo/demo_scheduler.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    copy2(cur_path, new_path)
    logger = Logger()
    notebook = Notebooks(logger)
    job = {
        "type": t_notebook,
        "path": new_path,
        "params": {},
        "value": "any",
        "status": t_add,
    }
    uid = str(uuid.uuid4())
    res = await notebook.exec(uid, job)
    print("\n\n\nres\n\n", res, "\n\n\n END")
    assert res is not None
    assert res.get("cells") is not None
    # TODO add more test
