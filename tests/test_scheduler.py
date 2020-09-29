from naas.types import t_add, t_health, t_scheduler
from naas.runner.logger import Logger
from naas.runner.jobs import Jobs
from naas.runner.scheduler import Scheduler
from naas.runner.notebooks import Notebooks
import getpass
import pytest  # noqa: F401
import uuid
import os
from shutil import copy2

user_folder_name = "test_user_folder"
user = getpass.getuser()


async def test_scheduler(tmp_path, event_loop):
    recur = "* * * * *"
    test_notebook = "tests/demo/demo_scheduler.ipynb"
    cur_path = os.path.join(os.getcwd(), test_notebook)
    new_path = os.path.join(tmp_path, test_notebook)
    os.makedirs(os.path.dirname(new_path))
    logger = Logger()
    notebooks = Notebooks(logger)
    jobs = Jobs(logger, True, [])
    scheduler = Scheduler(logger, jobs, notebooks, event_loop)
    uid = str(uuid.uuid4())
    copy2(cur_path, new_path)
    job = {
        "type": t_scheduler,
        "path": new_path,
        "params": {},
        "value": recur,
        "status": t_add,
    }
    await jobs.update(
        uid,
        job["path"],
        job["type"],
        job["value"],
        job["params"],
        job["status"],
    )
    resp_json = await jobs.list(uid)
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_add
    await scheduler.start(test_mode=True)
    resp_json = await jobs.list(uid)
    assert len(resp_json) == 1
    res_job = resp_json[0]
    assert res_job.get("type") == t_scheduler
    assert res_job.get("path") == new_path
    assert res_job.get("value") == recur
    assert res_job.get("status") == t_health
    # TODO add more tests
