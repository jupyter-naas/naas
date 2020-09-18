from flask import Flask, request, jsonify, send_file, redirect, Response, render_template, make_response
from .types import (t_delete, t_add, t_skip, t_update, t_error, t_static,
t_task, t_notebook, t_scheduler, t_dependency, t_main, t_health,t_start)
from apscheduler.schedulers.background import BackgroundScheduler
from sentry_sdk.integrations.flask import FlaskIntegration
from .proxy import escape_kubernet, encode_proxy_url
from flask_classful import FlaskView, route
from functools import wraps, update_wrapper
from .notifications import Notifications
from gevent.pywsgi import WSGIServer
import apscheduler.schedulers.base
from daemonize import Daemonize
from .logger import Logger
from time import strftime
import papermill as pm
from .jobs import Jobs
import pandas as pd
import pretty_cron
import sentry_sdk
import traceback
import datetime
import getpass
import shutil
import atexit
import gevent
import pycron
import base64
import errno
import uuid
import json
import time
import sys
import io
import os

class Runner(FlaskView):
    # Declare semaphore variable
    __name = 'naas_runner'
    __naas_folder = '.naas'
    __tasks_sem = None
    # Declare path variable
    __path_lib_files = os.path.dirname(os.path.abspath(__file__))
    __path_user_files = None
    __port = 5000
    __single_user_api_path = None
    __html_files = 'html'
    __assets_files = 'assets'
    __manager_index = 'manager.html'
    __manager_error = 'index.html'
    __log_filename = 'logs.csv'
    __tasks_files = 'jobs.json'
    __info_file = 'info.json'
    __app = None
    __http_server = None
    __notif = None
    __jobs = None
    __scheduler = None
    __daemon = None
    __user = None
    __sentry = None
    __logger = None
    excluded_methods = ['kill', 'start', 'test_client', 'get_app', 'get_test']
    route_base = '/v1'

    def __init__(self, path=None, port=None, user=None, public=None, proxy=None, testing=False):
        self.__path_user_files = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
        self.__path_user_files = path if path else self.__path_user_files
        self.__port = int(os.environ.get('NAAS_RUNNER_PORT', 5000))
        self.__port = int(port) if port else self.__port
        self.__user = os.environ.get('JUPYTERHUB_USER', 'joyvan@naas.com')
        self.__user = user if user else self.__user
        self.__public_url = os.environ.get('PUBLIC_DATASCIENCE', f'http://localhost:{self.__port}')
        self.__public_url = public if public else self.__public_url
        self.__proxy_url = os.environ.get('PUBLIC_PROXY_API', 'http://localhost:5002')
        self.__proxy_url = proxy if proxy else self.__proxy_url
        self.__tz = os.environ.get('TZ', 'Europe/Paris')
        self.__single_user_api_path = os.environ.get('SINGLEUSER_PATH', '.jupyter-single-user.dev.svc.cluster.local')
        self.__path_naas_files = os.path.join(self.__path_user_files, self.__naas_folder)
        self.__path_logs_file = os.path.join(self.__path_naas_files, self.__log_filename)
        self.__tasks_files_path = os.path.join(self.__path_naas_files, self.__tasks_files)
        self.__path_html_files = os.path.join(self.__path_lib_files, self.__html_files)
        self.__path_html_error = os.path.join(self.__path_lib_files, self.__manager_error)
        self.__path_manager_index = os.path.join(self.__path_html_files, self.__manager_index)
        self.__path_pidfile = os.path.join(self.__path_naas_files, f'{self.__name}.pid')
        self.__api_internal = f"http://jupyter-{escape_kubernet(self.__user)}{self.__single_user_api_path}:{self.__port}/{self.route_base}/"
        self.__init_naas_folder()
        # Init loggin system
        uid = str(uuid.uuid4())
        self.__logger = Logger()
        self.__notif = Notifications(self.__logger)
        self.__jobs = Jobs(uid, self.__logger)
        # Init scheduling system
        self.__scheduler = BackgroundScheduler()
        # Init http server
        self.__app = Flask(self.__name)
        self.__app.testing = testing
        self.__app.register_error_handler(404, self.__not_found)
        self.__app.register_error_handler(405, self.__not_allowed)
        self.__app.register_error_handler(500, self.__not_working)
        self.__app.register_error_handler(Exception, self.__exceptions)
        # Disable api cache
        self.__app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


    def __main(self):
        self.__init_scheduler()
        uid = str(uuid.uuid4())
        self.__logger.info(
            {'id': uid, 'type': t_main, "status": 'start API'})
        self.__sentry = sentry_sdk.init(
            dsn="https://28c6dea445f741a7a0c5e4db4df88df4@o448748.ingest.sentry.io/5430604",
            traces_sample_rate=1.0,
            environment=escape_kubernet(self.__user),
            integrations=[FlaskIntegration()]
        )
        self.__http_server = WSGIServer(('', 5000), self.__app)
        self.__http_server.serve_forever()

    def get_app(self):
        return self.__app
    
    def kill(self):
        if os.path.exists(self.__path_pidfile):
            try:
                with open(self.__path_pidfile, 'r') as f:
                    pid = f.read()
                    print('kill')
                    os.system(f'kill {pid}')
                    print(f'Deamon killed pid {pid}')
                    f.close()
            except Exception:
                print('No Deamon running')

    def get_test(self):
        self.__init_scheduler()
        self.register(self.__app)
        uid = str(uuid.uuid4())
        self.__logger.info({'id': uid, 'type': t_main, "status": 'start API'})
        app = self.get_app()
        app.app_context()
        return app.test_client()        

    def start(self, deamon=True):
        user = getpass.getuser()
        if (user != self.__user):
            raise Exception(f"{user} not autorized, use {self.__user} instead")
        self.kill()
        self.register(self.__app)
        if deamon:  
            self.__daemon = Daemonize(app=self.__name, pid=self.__path_pidfile, action=self.__main)
            print('Start Runner Deamon Mode')
            self.__daemon.start()
        else:
            print('Start Runner front Mode')
            self.__main()
                            
    def __get_res_nb(self, res):
        cells = res.get('cells')
        result = None
        result_type = None
        for cell in cells:
            outputs = cell.get('outputs', [])
            for output in outputs:
                metadata = output.get('metadata', [])
                data = output.get('data', dict())
                for meta in metadata:
                    if metadata[meta].get('naas_api'):
                        if (data.get('application/json')):
                            result_type = 'application/json'
                            result = data.get('application/json')
                        elif (data.get('text/html')):
                            result_type = 'text/html'
                            result = data.get('text/html')
                        elif (data.get('image/jpeg')):
                            result_type = 'image/jpeg'
                            result = data.get('image/jpeg')
                        elif (data.get('image/png')):
                            result_type = 'image/png'
                            result = data.get('image/png')
                        elif (data.get('image/svg+xml')):
                            result_type = 'image/svg+xml'
                            result = data.get('image/svg+xml')
                        if result_type is not None:
                            result = data.get(result_type)
        if result is None or result_type is None:
            return None
        return {'type': result_type, 'data': result}

    def __exec_job(self, uid, job):
        value = job.get('value', None)
        current_type = job.get('type', None)
        file_filepath = job.get('path')
        file_dirpath = os.path.dirname(file_filepath)
        file_filename = os.path.basename(file_filepath)
        file_filepath_out = os.path.join(file_dirpath, f'out_{file_filename}')
        params = job.get('params', dict())
        notif_down = params.get('notif_down', None)
        notif_up = params.get('notif_up', None)
        params['run_uid'] = uid
        start_time = time.time()
        res = None
        try:
            res = pm.execute_notebook(
                input_path=file_filepath,
                output_path=file_filepath_out,
                progress_bar=False,
                cwd=file_dirpath,
                parameters=params
            )
        except pm.PapermillExecutionError as err:
            self.__logger.error({'id': uid, 'type': 'PapermillExecutionError', "status": t_error,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out, 'error': str(err)})
            res = {"error": str(err)}
        except:
            tb = traceback.format_exc()
            res = {'error': str(tb)}
            self.__logger.error({'id': uid, 'type': 'Exception', "status": t_error,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out, 'error': str(tb)})
        if (not res):
            res = {'error': 'Unknow error'}
            self.__logger.error({'id': uid, 'type': 'Exception', "status": t_error,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out, 'error': res['error']})
        else:
            self.__logger.error({'id': uid, 'type': 'Exception', "status": t_health,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out})
        res['duration'] = (time.time() - start_time)
        if(res.get('error')):
            self.__notif.send_error(uid, str(res.get('error')), file_filepath)
            if (notif_down and current_type == t_scheduler):
                self.__notif.send_scheduler(uid, 'down', notif_down, file_filepath, value)
            elif (notif_down):
                self.__notif.send(uid, 'down', notif_down, file_filepath, current_type)
        elif (notif_up and current_type == t_scheduler):
            self.__notif.send_scheduler(uid, 'up', notif_down, file_filepath, value)
        elif (notif_up):
            self.__notif.send(uid, 'up', notif_up, file_filepath, current_type)
        return res

    def __html_error(self, content):
        try:
            with open(self.__path_html_error, 'r') as f:
                template = f.read()
                f.close()
                return template.replace('{ERROR}', content)
        except Exception:
            print('Cannot get html error')
            return ''

    def __init_naas_folder(self):
        if not os.path.exists(self.__path_naas_files):
            try:
                os.makedirs(self.__path_naas_files)
                os.system(f'chown -R ftp {self.__path_naas_files}')
                print('Created brain')
            except Exception:
                print('No need to create brain', Exception)

    def __send_response(self, uid, res, t_notebook, duration, params):
        next_url = params.get('next_url', None)
        if next_url is not None:
            if "http" not in next_url:
                next_url = f'{self.__api_internal}{next_url}'
            self.__logger.info(
                {'id': uid, 'type': t_notebook, 'status': 'next_url', 'url': next_url})
            return redirect(next_url, code=302)
        else:
            res_data = self.__get_res_nb(res)
            if res_data and res_data.get('type') == 'application/json':
                return jsonify(res_data.get('data')), 200
            elif res_data:
                return Response(res_data.get('data'), mimetype=res_data.get('type'))
            else:
                return jsonify({'id': uid, "status": "Done", "time": duration}), 200


    def __is_running(self, uid, notebook_filepath, target_type):
        cur_job = self.__jobs.find_by_path(uid, notebook_filepath, target_type)
        if cur_job:
            status = cur_job.get('status', None)
            if (status and status == t_start):
                return True
        return False


    def __scheduler_greenlet(self, main_uid, current_time, task):
        value = task.get('value', None)
        current_type = task.get('type', None)
        file_filepath = task.get('path')
        params = task.get('params', dict())
        uid = str(uuid.uuid4())
        running = self.__is_running(uid, file_filepath, current_type)
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

    def __init_scheduler(self):
        if (self.__scheduler.state != apscheduler.schedulers.base.STATE_RUNNING):
            self.__scheduler.add_job(func=self.__scheduler_function,
                            trigger="interval", seconds=60, max_instances=10)
            self.__scheduler.start()
            atexit.register(lambda: self.__scheduler.shutdown())
            uid = str(uuid.uuid4())
            self.__logger.info({'id': uid, 'type': t_main, "status": 'start SCHEDULER'})

    def __scheduler_function(self):
        # Create unique for scheduling step (one step every minute)
        main_uid = str(uuid.uuid4())
        try:
            current_time = datetime.datetime.now()
            all_start_time = time.time()
            greelets = []
            # Write self.__scheduler init info in self.__logger.write
            self.__logger.info({'id': main_uid, 'type': t_scheduler,
                                    'status': t_start})
            if os.path.exists(self.__tasks_files_path):
                for job in  self.__jobs.list(main_uid):
                    g = gevent.spawn(self.__scheduler_greenlet,
                                    main_uid, current_time, job)
                    greelets.append(g)
                gevent.joinall(greelets)
            else:
                self.__logger.error({'id': main_uid, 'type': t_scheduler, 'status': t_error,
                                        "error": '__tasks_files_path', 'path': self.__tasks_files_path})
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

    def __version(self):
        version = None
        try:
            with open(os.path.join(self.__path_lib_files, self.__info_file), 'r') as json_file:
                version = json.load(json_file)
        except:
            version = {'error': 'cannot get info.json'}
        return version
    
    def __not_found(self, error):
        uid = str(uuid.uuid4())
        self.__logger.error({'id': uid, 'type': 'request error',
                                "status": '404', 'error': str(error)})
        return jsonify({'id': uid, 'error': 'Not found'}), 404

    def __not_allowed(self, error):
        uid = str(uuid.uuid4())
        self.__logger.error({'id': uid, 'type': 'request error',
                                "status": '405', 'error': str(error)})
        return jsonify({'id': uid, 'error': 'Method not allowed. The method is not allowed for the requested URL.'}), 405

    def __not_working(self, error):
        uid = str(uuid.uuid4())
        self.__logger.error({'id': uid, 'type': 'request error',
                                "status": '500', 'error': str(error)})
        return jsonify({'error': 'Something wrong happen'}), 500

    def __exceptions(self, e):
        uid = str(uuid.uuid4())
        tb = traceback.format_exc()
        self.__logger.error({'id': uid, 'type': 'Exception', 'method': request.method, 'status': t_error, 'addr': request.remote_addr,
                                'scheme': request.scheme, 'full_path': request.full_path, 'error': str(e), 'trace': tb})
        return jsonify({'error':  str(e)}), 500
    
    def after_request(self, name, response):
        uid = str(uuid.uuid4())
        self.__logger.info({'id': uid, 'type': 'request', 'method': request.method, 'status': response.status,
                                'addr': request.remote_addr, 'scheme': request.scheme, 'full_path': request.full_path})
        response.headers["Pragma"] = "no-cache"
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Expires'] = '-1'
        return response

    @route('/')
    def index(self):
        uid = str(uuid.uuid4())
        self.__logger.info(
            {'id': uid, 'type': t_static, 'status': 'send', 'filepath': self.__path_manager_index})
        return send_file(self.__path_manager_index), 200

    @route('/env')
    def env(self):
        env = {
            'status': t_health,
            'version': self.__version(),
            'JUPYTERHUB_USER': self.__user,
            'PUBLIC_DATASCIENCE': self.__public_url,
            'PUBLIC_PROXY_API': self.__proxy_url,
            'TZ': self.__tz
            
        }
        return jsonify(env), 200
    
    @route('/scheduler')
    def scheduler(self):
        status = 'stopped'
        print('self.__scheduler.state', self.__scheduler.state)
        if (self.__scheduler.state == apscheduler.schedulers.base.STATE_RUNNING):
            status = 'running'
        elif (self.__scheduler.state == apscheduler.schedulers.base.STATE_PAUSED):
            status = 'paused'
        return jsonify({"status": status}), 200
    
    @route('/scheduler/<mode>')
    def set_scheduler(self, mode: str):
        if (mode == 'pause'):
            self.__scheduler.pause()
        elif (mode == 'resume'):
            self.__scheduler.resume()
        status = 'stopped'
        if (self.__scheduler.state == apscheduler.schedulers.base.STATE_RUNNING):
            status = 'running'
        elif (self.__scheduler.state == apscheduler.schedulers.base.STATE_PAUSED):
            status = 'paused'
        return jsonify({"status": status}), 200

    @route('/logs')
    def logs(self):
        as_file = request.args.get('as_file', False)
        if as_file:
            res = send_file(self.__logger.get_file_path(), attachment_filename='logs.csv')
            return res
        else:
            uid = str(uuid.uuid4())
            limit = int(request.args.get('limit', 0))
            skip = int(request.args.get('skip', 0))
            search = str(request.args.get('search', ''))
            filters = list(request.args.get('filters', []))
            logs = self.__logger.list(uid, skip, limit, search, filters)
            # self.__logger.info(
                # {'id': uid, 'type': t_static, 'status': 'send', 'filepath': 'logs', 'skip': skip, 'limit': limit, 'search': search, 'filters': filters}))
            return jsonify(logs), 200

    @route('/jobs')
    def get(self):
        uid = str(uuid.uuid4())
        status = self.__jobs.list(uid)
        self.__logger.info(
            {'id': uid, 'type': t_static, 'status': 'send', 'filepath': 'status'})
        return jsonify(status), 200
    
    @route('/jobs')
    def post(self):
        uid = str(uuid.uuid4())
        data = request.get_json()
        if not request.is_json:
            self.__logger.info(
                {'id': uid, 'type': t_task, 'status': t_error, 'error': 'not json'})
            return jsonify({'result': 'not json'}), 400
        if not data or ["path", "type", "params", "value", "status"].sort() != list(data.keys()).sort():
            self.__logger.info(
                {'id': uid, 'type': t_task, 'status': t_error, 'error': 'missing keys', 'tb': data})
            return jsonify({'result': 'missing keys', }), 400
        updated = self.__jobs.update(uid, 
            data['path'], data['type'], data['value'], data['params'], data['status'])
        self.__logger.info(
            {'id': uid, 'type': t_task, 'status': updated['status']})
        return jsonify(updated), 200

    @route(f'/{t_static}/up')
    def resUp(self):
        file_filename = 'up.png'
        file_filepath = os.path.join(self.__path_lib_files, self.__assets_files, file_filename)
        try:
            res = send_file(file_filepath, attachment_filename=file_filename)
            return res
        except Exception as e:
            return self.__html_error(json.dumps({"error": e})), 404
        
    @route(f'/{t_static}/down')
    def resDown(self):
        file_filename = 'down.png'
        file_filepath = os.path.join(self.__path_lib_files, self.__assets_files, file_filename)
        try:
            res = send_file(file_filepath, attachment_filename=file_filename)
            return res
        except Exception as e:
            return self.__html_error(json.dumps({"error": e})), 404
        
    @route(f'/{t_static}/<token>')
    def resStatic(self, token: str):
        uid = str(uuid.uuid4())
        task = self.__jobs.find_by_value(uid, token, t_static)
        if task:
            file_filepath = task.get('path')
            file_filename = os.path.basename(file_filepath)
            params = task.get('params', dict())
            self.__logger.info(
                {'id': uid, 'type': t_static, 'status': t_start, 'filepath': file_filepath, 'token': token})
            try:
                self.__jobs.update(uid, file_filepath, t_static, token,
                            params, t_health, 1)
                res = send_file(file_filepath, attachment_filename=file_filename)
                self.__logger.info(
                    {'id': uid, 'type': t_static, 'status': t_start, 'filepath': file_filepath, 'token': token})
                return res
            except Exception as e:
                self.__logger.error(
                    {'id': uid, 'type': t_static, 'status': t_error, 'filepath': file_filepath, 'token': token, "error": e})
                self.__jobs.update(uid, file_filepath, t_static,
                            token, params, t_error, 1)
                return self.__html_error(json.dumps({'id': uid, "error": e})), 404
        self.__logger.error({'id': uid, 'type': t_static, 'status': t_error,
                                "error": 'Cannot find your token', 'token': token})
        return self.__html_error(json.dumps({'id': uid, "error": "Cannot find your token", 'token': token})), 401


    @route(f'/{t_notebook}/<token>')
    def startNotebook(self, token: str):
        uid = str(uuid.uuid4())
        task = self.__jobs.find_by_value(uid, token, t_notebook)
        if task:
            value = task.get('value', None)
            file_filepath = task.get('path')
            task['params'] = {**(task.get('params', dict())), **(request.args)}
            self.__logger.info(
                {'id': uid, 'type': t_notebook, 'status': t_start, 'filepath': file_filepath, 'token': token})
            res = self.__exec_job(uid, task)
            if (res.get('error')):
                self.__logger.error({'main_id': uid, 'id': uid, 'type': t_notebook, 'status': t_error,
                                        'filepath': file_filepath, 'duration': res.get('duration'), 'error': res.get('error')})
                self.__jobs.update(uid, file_filepath, t_notebook, value, task.get(
                    'params'), t_error, res.get('duration'))
                return jsonify({'id': uid, "error": res.get('error')}), 200
            self.__logger.info(
                {'main_id': uid, 'id': uid, 'type': t_notebook, 'status': t_health, 'filepath': file_filepath, 'duration': res.get('duration')})
            self.__jobs.update(uid, file_filepath, t_notebook, value, task.get(
                'params'), t_health, res.get('duration'))
            return self.__send_response(uid, res, t_notebook, res.get('duration'), task.get('params'))
        self.__logger.error({'id': uid, 'type': t_notebook, 'status': t_error,
                                'token': token, 'error': 'Cannot find your token'})
        return jsonify({'id': uid, "error": "Cannot find your token"}), 401
