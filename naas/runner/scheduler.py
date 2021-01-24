from naas.types import t_scheduler, t_start, t_main, t_health, t_error, t_busy
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import apscheduler.schedulers.base
from .env_var import n_env
import traceback
import datetime
import asyncio
import aiohttp
import pycron
import time
import uuid


async def fetch(url):
    with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=n_env.scheduler_timeout) as response:
            return await response.json()


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

    def stop(self):
        if self.__scheduler is not None:
            self.__scheduler.pause()
            self.__scheduler.remove_job(n_env.scheduler_job_name)
            self.__scheduler.shutdown(wait=False)
            self.__scheduler = None

    async def start(self, test_mode=False):
        if test_mode:
            await self.__scheduler_function()
        else:
            if self.__scheduler.state != apscheduler.schedulers.base.STATE_RUNNING:
                self.__scheduler.add_job(
                    func=self.__scheduler_function,
                    trigger="interval",
                    id=n_env.scheduler_job_name,
                    seconds=n_env.scheduler_interval,
                    max_instances=n_env.scheduler_job_max,
                )
                self.__scheduler.start()
                uid = str(uuid.uuid4())
                self.__logger.info(
                    {
                        "id": uid,
                        "type": t_main,
                        "filepath": "sheduler",
                        "status": f"start SCHEDULER seconds={n_env.scheduler_interval}, max_instances={n_env.scheduler_job_max}",
                    }
                )

    async def __check_run(self, uid, file_filepath, current_type, last_update_str):
        running = await self.__jobs.is_running(uid, file_filepath, current_type)
        if last_update_str and running:
            try:
                last_update = datetime.datetime.strptime(
                    last_update_str, "%d/%m/%y %H:%M:%S"
                )
                # Timeout run 1h
                timeout_date = datetime.datetime.today() - datetime.timedelta(hours=1)
                running = True if last_update > timeout_date else False
            except ValueError:
                pass
        return running

    async def __scheduler_greenlet(self, main_uid, current_time, task):
        value = task.get("value", None)
        current_type = task.get("type", None)
        file_filepath = task.get("path", None)
        last_update = task.get("lastUpdate", None)
        params = task.get("params", dict())
        uid = str(uuid.uuid4())
        try:
            running = await self.__check_run(
                uid, file_filepath, current_type, last_update
            )
            if (
                current_type == t_scheduler
                and value is not None
                and pycron.is_now(value, current_time)
                and not running
            ):
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
                next_url = params.get("next_url", None)
                if next_url is not None and "https://" not in next_url:
                    self.__logger.error(
                        {
                            "id": uid,
                            "type": t_scheduler,
                            "status": "next_url",
                            "filepath": file_filepath,
                            "url": next_url,
                            "error": "url not in right format",
                        }
                    )
                elif next_url is not None and "https://" in next_url:
                    self.__logger.info(
                        {
                            "id": uid,
                            "type": t_scheduler,
                            "status": "next_url",
                            "filepath": file_filepath,
                            "url": next_url,
                        }
                    )
                    try:
                        await fetch(url=next_url)
                    except:  # noqa: E722
                        tb = traceback.format_exc()
                        self.__logger.error(
                            {
                                "id": main_uid,
                                "type": t_scheduler,
                                "status": t_error,
                                "filepath": file_filepath,
                                "error": "Error in next_url",
                                "trace": str(tb),
                            }
                        )
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
            elif running:
                self.__logger.info(
                    {
                        "main_id": str(main_uid),
                        "id": uid,
                        "type": t_scheduler,
                        "status": t_busy,
                        "filepath": file_filepath,
                    }
                )
        except:  # noqa: E722
            tb = traceback.format_exc()
            self.__logger.error(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "status": t_error,
                    "filepath": file_filepath,
                    "error": "Unknow error",
                    "trace": str(tb),
                }
            )
            await self.__jobs.update(
                uid,
                file_filepath,
                t_scheduler,
                value,
                params,
                t_error,
            )

    async def __scheduler_function(self):
        # Create unique for scheduling step (one step every minute)
        main_uid = str(uuid.uuid4())
        all_start_time = time.time()
        try:
            if n_env.scheduler_interval == 60:
                current_time = datetime.datetime.now()
            elif n_env.scheduler_interval == 1:
                # for speed test in ci
                current_time = datetime.datetime.now()
                current_sec = current_time.second
                current_time = current_time.replace(minute=current_sec)
            else:
                raise ValueError(
                    f"naas doesn't support NAAS_SCHEDULER_TIME={n_env.scheduler_interval}"
                )
            print(f"\n\n================ {current_time} ============== \n\n")
            self.__logger.info(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "filepath": "scheduler",
                    "status": t_start,
                }
            )
            jobs = await self.__jobs.list(main_uid)
            await asyncio.gather(
                *[
                    self.__scheduler_greenlet(main_uid, current_time, job)
                    for job in jobs
                ]
            )
            duration_total = time.time() - all_start_time
            self.__logger.info(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "filepath": "scheduler",
                    "status": t_health,
                    "duration": duration_total,
                }
            )
        except Exception as e:
            tb = traceback.format_exc()
            duration_total = time.time() - all_start_time
            self.__logger.error(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "status": t_error,
                    "filepath": "scheduler",
                    "duration": duration_total,
                    "error": str(e),
                    "trace": tb,
                }
            )
        except:  # noqa: E722
            tb = traceback.format_exc()
            duration_total = time.time() - all_start_time
            self.__logger.error(
                {
                    "id": main_uid,
                    "type": t_scheduler,
                    "status": t_error,
                    "filepath": "scheduler",
                    "duration": duration_total,
                    "error": "Unknow error",
                    "trace": tb,
                }
            )
