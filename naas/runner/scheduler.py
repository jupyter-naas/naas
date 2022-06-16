from naas.ntypes import (
    t_scheduler,
    t_start,
    t_main,
    t_health,
    t_error,
    t_busy,
    t_delete,
    t_out_of_credits,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from naas.callback import Callback
import apscheduler.schedulers.base
from .env_var import n_env
import traceback
import requests
import datetime
import asyncio
import pycron
import time
import pytz
import uuid
import os

from naas_drivers import naascredits
import pydash as _


async def fetch(url):
    return requests.get(url, timeout=n_env.scheduler_timeout).json()


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
        print("Stop scheduler")
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

    async def __scheduler_greenlet(self, main_uid, current_time, job):
        value = job.get("value")
        current_type = job.get("type")
        file_filepath = job.get("path")
        last_update = job.get("lastUpdate")
        status = job.get("status")
        params = job.get("params", dict())
        uid = str(uuid.uuid4())
        try:
            running = await self.__check_run(
                uid, file_filepath, current_type, last_update
            )
            if (
                current_type == t_scheduler
                and value is not None
                and pycron.is_now(value, current_time)
                and status != t_delete
                and not running
            ):
                if not os.environ.get(
                    "JUPYTERHUB_API_TOKEN"
                ) is None and "app.naas.ai" in os.environ.get("JUPYTERHUB_URL", ""):
                    if _.get(naascredits.connect().get_balance(), "balance") <= 0:
                        self.__logger.info(
                            {
                                "main_id": str(main_uid),
                                "id": uid,
                                "type": t_scheduler,
                                "status": t_out_of_credits,
                                "filepath": file_filepath,
                            }
                        )
                        return
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
                res = await self.__nb.exec(uid, job.copy())
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
                        r = await fetch(url=next_url)
                        self.__logger.info(
                            {
                                "id": uid,
                                "type": t_scheduler,
                                "status": r,
                                "filepath": file_filepath,
                                "url": next_url,
                            }
                        )
                    except Exception as e:  # noqa: E722
                        tb = traceback.format_exc()
                        self.__logger.error(
                            {
                                "id": main_uid,
                                "type": t_scheduler,
                                "status": t_error,
                                "filepath": file_filepath,
                                "error": f"Error while calling next_url: exception[{str(e)}] traceback[{str(tb)}]",
                                "traceback": str(tb),
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
                    "traceback": str(tb),
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

    def getTerminals(self):
        try:
            r = requests.get(
                f"{n_env.user_url}/api/terminals",
                headers={
                    "Authorization": f"token {n_env.token}",
                },
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(e)
            return {}

    def getSessions(self):
        try:
            r = requests.get(
                f"{n_env.user_url}/api/sessions",
                headers={
                    "Authorization": f"token {n_env.token}",
                },
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(e)
            return {}

    async def analytics(self, uid):
        try:
            curdate = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
            data = {
                "date": curdate,
                "gpu": os.environ.get("NAAS_GPU", "NO"),
                "jobs": await self.__jobs.list(uid),
                "kernels": self.getSessions(),
                "terminals": self.getTerminals(),
            }
            if n_env.report_callback:
                Callback().add(
                    auto_delete=False,
                    uuid=f"naas_analytics__{curdate}",
                    default_result=data,
                    no_override=True,
                )
        except Exception as e:
            tb = traceback.format_exc()
            self.__logger.error(
                {
                    "id": uid,
                    "type": t_scheduler,
                    "filepath": "analytics",
                    "status": t_error,
                    "error": str(e),
                    "traceback": tb,
                }
            )

    async def __scheduler_function(self):
        # Create unique for scheduling step (one step every minute)
        main_uid = str(uuid.uuid4())
        all_start_time = time.time()
        try:
            if n_env.scheduler_interval == 60:
                current_time = datetime.datetime.now(tz=pytz.timezone(n_env.tz))
            elif n_env.scheduler_interval == 1:
                # for speed test in ci
                current_time = datetime.datetime.now(tz=pytz.timezone(n_env.tz))
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
            jobs = await self.__jobs.list(main_uid, prodPath=True)
            await asyncio.gather(
                *[
                    self.__scheduler_greenlet(main_uid, current_time, job)
                    for job in jobs
                ],
                return_exceptions=False,
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
            # We disable this for now as it is not used and is therefore filling up the database.
            # await self.analytics(main_uid)
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
                    "traceback": tb,
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
                    "traceback": tb,
                }
            )
