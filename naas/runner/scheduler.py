# from apscheduler.schedulers.background import BackgroundScheduler
from naas.types import t_scheduler, t_start, t_main, t_health, t_error
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import apscheduler.schedulers.base
import asyncio
import traceback
import datetime
import time
import uuid
import sys

class Scheduler():
    __scheduler = None
    __logger = None
    __jobs = None

    def __init__(self, logger, jobs, loop):
        self.__logger = logger
        self.__jobs = jobs
        # self.__scheduler = BackgroundScheduler()
        self.__scheduler = AsyncIOScheduler({'event_loop': loop})
        self.state = self.__scheduler.state

    def status(self):
        if (self.__scheduler.state == apscheduler.schedulers.base.STATE_RUNNING):
            return 'running'
        elif (self.__scheduler.state == apscheduler.schedulers.base.STATE_PAUSED):
            return 'paused'

    def start(self):
        if (self.__scheduler.state != apscheduler.schedulers.base.STATE_RUNNING):
            self.__scheduler.add_job(func=self.__scheduler_function,
                            trigger="interval", seconds=60, max_instances=10)
            self.__scheduler.start()
            uid = str(uuid.uuid4())
            self.__logger.info({'id': uid, 'type': t_main, "status": 'start SCHEDULER'})

    def __scheduler_greenlet(self, main_uid, current_time, task):
        value = task.get('value', None)
        current_type = task.get('type', None)
        file_filepath = task.get('path')
        params = task.get('params', dict())
        uid = str(uuid.uuid4())
        running = self.__jobs.is_running(uid, file_filepath, current_type)
        if current_type == t_scheduler and value is not None and pycron.is_now(value, current_time) and not running:
            self.__logger.info(
                {'main_id': str(main_uid), 'id': uid, 'type': t_scheduler, 'status': t_start, 'filepath': file_filepath})
            self.__jobs.update(uid, file_filepath, t_scheduler, value, params, t_start)
            res = self.__exec_job(uid, task)
            if (res.get('error')):
                self.__logger.error({'main_id': str(main_uid), 'id': uid, 'type': t_scheduler, 'status': t_error,
                                        'filepath': file_filepath, 'duration': res.get('duration'), 'error': str(res.get('error'))})
                self.__jobs.update(uid, file_filepath, t_scheduler, value,
                            params, t_error, res.get('duration'))
                return
            self.__logger.info(
                {'main_id': str(main_uid), 'id': uid, 'type': t_scheduler, 'status': t_health, 'filepath': file_filepath, 'duration': res.get('duration')})
            self.__jobs.update(uid, file_filepath, t_scheduler, value, params,
                        t_health, res.get('duration'))
            
    async def __scheduler_function(self):
        # Create unique for scheduling step (one step every minute)
        main_uid = str(uuid.uuid4())
        try:
            current_time = datetime.datetime.now()
            all_start_time = time.time()
            greelets = []
            # Write self.__scheduler init info in self.__logger.write
            self.__logger.info({'id': main_uid, 'type': t_scheduler,
                                    'status': t_start})
            for job in  self.__jobs.list(main_uid):
                g = asyncio.ensure_future(self.__scheduler_greenlet(main_uid, current_time, job))
                # g = gevent.spawn(self.__scheduler_greenlet,
                #                 main_uid, current_time, job)
                greelets.append(g)
            await asyncio.gather(*greelets)
            # gevent.joinall(greelets)
            durationTotal = (time.time() - all_start_time)
            self.__logger.info({'id': main_uid, 'type': t_scheduler, 'status': t_health, 'duration': durationTotal})
        except Exception as e:
            tb = traceback.format_exc()
            durationTotal = (time.time() - all_start_time)
            self.__logger.error({'id': main_uid, 'type': t_scheduler, 'status': t_error,
                                    'duration': durationTotal, 'error': str(e), 'trace': tb})
        except:
            tb = traceback.format_exc()
            durationTotal = (time.time() - all_start_time)
            self.__logger.error({'id': main_uid, 'type': t_scheduler, 'status': t_error,
                                    'duration': durationTotal, 'error': str(sys.exc_info()[0]), 'trace': tb})

