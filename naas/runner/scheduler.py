from naas.types import t_scheduler, t_start, t_main, t_health, t_error
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import apscheduler.schedulers.base
import traceback
import datetime

# import nest_asyncio
import asyncio
import pycron
import time
import uuid

# TODO remove this fix when papermill support uvloop of Sanic support option to don't use uvloop
# asyncio.set_event_loop_policy(None)
# nest_asyncio.apply()


class Scheduler:
    __scheduler = None
    __nb = None
    __logger = None
    __jobs = None

    def __init__(self, logger, jobs, notebooks, loop):
        self.__logger = logger
        self.__nb = notebooks
        self.__jobs = jobs
        self.__scheduler = AsyncIOScheduler({"event_loop": loop})
        self.state = self.__scheduler.state

    def status(self):
        if self.__scheduler.state == apscheduler.schedulers.base.STATE_RUNNING:
            return "running"
        elif self.__scheduler.state == apscheduler.schedulers.base.STATE_PAUSED:
            return "paused"

    def start(self):
        if self.__scheduler.state != apscheduler.schedulers.base.STATE_RUNNING:
            self.__scheduler.add_job(
                func=self.__scheduler_function,
                trigger="interval",
                seconds=60,
                max_instances=10,
            )
            self.__scheduler.start()
            uid = str(uuid.uuid4())
            self.__logger.info({"id": uid, "type": t_main, "status": "start SCHEDULER"})

    async def __scheduler_greenlet(self, main_uid, current_time, task):
        print("__scheduler_greenlet => start")
        try:
            value = task.get("value", None)
            current_type = task.get("type", None)
            file_filepath = task.get("path")
            params = task.get("params", dict())
            uid = str(uuid.uuid4())
            running = await self.__jobs.is_running(uid, file_filepath, current_type)
            if (
                current_type == t_scheduler
                and value is not None
                and pycron.is_now(value, current_time)
                and not running
            ):
                print("__scheduler_greenlet => right time")
                self.__logger.info(
                    {
                        "main_id": str(main_uid),
                        "id": uid,
                        "type": t_scheduler,
                        "status": t_start,
                        "filepath": file_filepath,
                    }
                )
                await self.__jobs.update(
                    uid, file_filepath, t_scheduler, value, params, t_start
                )
                res = await self.__nb.exec(uid, task)
                if res.get("error"):
                    self.__logger.error(
                        {
                            "main_id": str(main_uid),
                            "id": uid,
                            "type": t_scheduler,
                            "status": t_error,
                            "filepath": file_filepath,
                            "duration": res.get("duration"),
                            "error": str(res.get("error")),
                        }
                    )
                    await self.__jobs.update(
                        uid,
                        file_filepath,
                        t_scheduler,
                        value,
                        params,
                        t_error,
                        res.get("duration"),
                    )
                    return
                self.__logger.info(
                    {
                        "main_id": str(main_uid),
                        "id": uid,
                        "type": t_scheduler,
                        "status": t_health,
                        "filepath": file_filepath,
                        "duration": res.get("duration"),
                    }
                )
                await self.__jobs.update(
                    uid,
                    file_filepath,
                    t_scheduler,
                    value,
                    params,
                    t_health,
                    res.get("duration"),
                )
                print("__scheduler_greenlet => runned")
            else:
                print("__scheduler_greenlet => NOT runned")
        except:  # noqa: E722
            tb = traceback.format_exc()
            self.__logger.error(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "status": t_error,
                    "error": "Unknow error",
                    "trace": str(tb),
                }
            )

    async def __scheduler_function(self):
        # Create unique for scheduling step (one step every minute)
        main_uid = str(uuid.uuid4())
        try:
            current_time = datetime.datetime.now()
            all_start_time = time.time()
            # Write self.__scheduler init info in self.__logger.write
            self.__logger.info({"id": main_uid, "type": t_scheduler, "status": t_start})
            jobs = await self.__jobs.list(main_uid)
            await asyncio.gather(
                *[
                    self.__scheduler_greenlet(main_uid, current_time, job)
                    for job in jobs
                ]
            )
            durationTotal = time.time() - all_start_time
            self.__logger.info(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "status": t_health,
                    "duration": durationTotal,
                }
            )
        except Exception as e:
            tb = traceback.format_exc()
            durationTotal = time.time() - all_start_time
            self.__logger.error(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "status": t_error,
                    "duration": durationTotal,
                    "error": str(e),
                    "trace": tb,
                }
            )
        except:  # noqa: E722
            tb = traceback.format_exc()
            durationTotal = time.time() - all_start_time
            self.__logger.error(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "status": t_error,
                    "duration": durationTotal,
                    "error": "Unknow error",
                    "trace": tb,
                }
            )
