from .types import (t_delete, t_add, t_skip, t_edited, t_error, t_static,
t_task, t_notebook, t_scheduler, t_dependency, t_main, t_health,t_start)
from flask import Flask, request, jsonify, send_file, redirect, Response, render_template, make_response
from apscheduler.schedulers.background import BackgroundScheduler
from functools import wraps, update_wrapper
from gevent.pywsgi import WSGIServer
from .proxy import escape_kubernet, get_proxy_url
from .logger import Logger
from .notifications import Notifications
import apscheduler.schedulers.base
from daemonize import Daemonize
from time import strftime
import papermill as pm
from .jobs import Jobs
import pandas as pd
import pretty_cron
import traceback
import datetime
import getpass
import string
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

class Runner():
    # Declare semaphore variable
    __name = 'naas_runner'
    __naas_file = '.naas'
    __tasks_sem = None
    # Declare path variable
    __path_lib_files = os.getcwd()
    __path_user_files = os.environ.get('JUPYTER_SERVER_ROOT', '/home/ftp')
    __port = int(os.environ.get('NAAS_RUNNER_PORT', 5000))
    __version_API = 'v1'
    __single_user_api_path = os.environ.get('SINGLEUSER_PATH', '.jupyter-single-user.dev.svc.cluster.local')
    __html_files = 'html'
    __assets_files = 'assets'
    __manager_index = 'index.html'
    __manager_error = 'index.html'
    __log_filename = 'logs.csv'
    __tasks_files = 'tasks.json'
    __info_file = 'info.json'

    app = None

    def __init__(self, skip, port):
        self.__path_naas_files = os.path.join(self.__path_user_files, self.__naas_file)
        self.__path_logs_file = os.path.join(self.__path_naas_files, self.__log_filename)
        self.__tasks_files_path = os.path.join(self.__path_naas_files, self.__tasks_files)
        self.__path_html_files = os.path.join(self.__path_lib_files, self.__html_files)
        self.__path_html_error = os.path.join(self.__path_lib_files, self.__manager_error)
        self.__path_manager_index = os.path.join(self.__path_html_files, self.__manager_index)
        self.__path_pidfile = os.path.join(self.__path_naas_files, f'{self.__name}.pid')
        self.__port = int(port) if port else self.__port
        self.__api_internal = f"http://jupyter-{escape_kubernet(os.environ.get('JUPYTERHUB_USER'))}{self.__single_user_api_path}:{self.__port}/{self.__version_API}/"
        if skip is True:
            self.init_naas_folder()

    def kill(self):
        try:
            with open(self.__path_pidfile, 'r') as f:
                pid = f.read()
                print('kill')
                os.system(f'kill {pid}')
                print(f'Deamon killed pid {pid}')
                f.close()
        except Exception:
            print('No Deamon running')

    def __main(self):
        uid = str(uuid.uuid4())
        self.logger.write.info(json.dumps(
            {'id': uid, 'type': t_main, "status": 'start API'}))
        self.http_server = WSGIServer(('', 5000), self.app)
        self.http_server.serve_forever()

    def start(self):
        uid = str(uuid.uuid4())
        user = getpass.getuser()
        if (user == 'root'):
            raise Exception(f"root not autorized, use {os.environ.get('JUPYTERHUB_USER')} instead")
        # Init loggin system
        self.logger = Logger()
        self.notif = Notifications(self.logger)
        self.jobs = Jobs(uid, self.logger)
        # Init scheduling system
        self.scheduler = BackgroundScheduler()
        # Init http server
        self.app = Flask(self.__name)
        # Disable api cache
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        self.daemon = Daemonize(app=self.__name, pid=self.__path_pidfile, action=self.__main)
        print('Start new Deamon')
        self.daemon.start()
                            
    def version(self):
        try:
            with open(os.path.join(self.__path_lib_files, self.__info_file), 'r') as json_file:
                version = json.load(json_file)
                return version
        except:
            return {'error': 'cannot get info.json'}


    def get_res_nb(self, res):
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

    def exec_job(self, uid, job):
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
            self.logger.write.error(json.dumps({'id': uid, 'type': 'PapermillExecutionError', "status": t_error,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out, 'error': str(err)}))
            res = {"error": str(err)}
        except:
            tb = traceback.format_exc()
            res = {'error': str(tb)}
            self.logger.write.error(json.dumps({'id': uid, 'type': 'Exception', "status": t_error,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out, 'error': str(tb)}))
        if (not res):
            res = {'error': 'Unknow error'}
            self.logger.write.error(json.dumps({'id': uid, 'type': 'Exception', "status": t_error,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out, 'error': res['error']}))
        else:
            self.logger.write.error(json.dumps({'id': uid, 'type': 'Exception', "status": t_health,
                                    'filepath': file_filepath, 'output_filepath': file_filepath_out}))
        res['duration'] = (time.time() - start_time)
        if(res.get('error')):
            self.notif.send_error(uid, str(res.get('error')), file_filepath)
            if (notif_down and current_type == t_scheduler):
                self.notif.send_scheduler(uid, 'down', notif_down, file_filepath, value)
            elif (notif_down):
                self.notif.send(uid, 'down', notif_down, file_filepath, current_type)
        elif (notif_up and current_type == t_scheduler):
            self.notif.send_scheduler(uid, 'up', notif_down, file_filepath, value)
        elif (notif_up):
            self.notif.send(uid, 'up', notif_up, file_filepath, current_type)
        return res

    @app.errorhandler(404)
    def not_found(self, error):
        uid = str(uuid.uuid4())
        self.logger.write.error(json.dumps({'id': uid, 'type': 'request error',
                                "status": '404', 'error': str(error)}))
        return jsonify({'id': uid, 'error': 'Not found'}), 404


    @app.errorhandler(405)
    def not_allowed(self, error):
        uid = str(uuid.uuid4())
        self.logger.write.error(json.dumps({'id': uid, 'type': 'request error',
                                "status": '405', 'error': str(error)}))
        return jsonify({'id': uid, 'error': 'Method not allowed. The method is not allowed for the requested URL.'}), 405


    @app.errorhandler(500)
    def not_working(self, error):
        uid = str(uuid.uuid4())
        self.logger.write.error(json.dumps({'id': uid, 'type': 'request error',
                                "status": '500', 'error': str(error)}))
        return jsonify({'error': 'Something wrong happen'}), 500


    @app.after_request
    def after_request(self, response):
        uid = str(uuid.uuid4())
        self.logger.write.info(json.dumps({'id': uid, 'type': 'request', 'method': request.method, 'status': response.status,
                                'addr': request.remote_addr, 'scheme': request.scheme, 'full_path': request.full_path}))
        response.headers["Pragma"] = "no-cache"
        response.headers['Last-Modified'] = datetime.datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Expires'] = '-1'
        return response


    @app.errorhandler(Exception)
    def exceptions(self, e):
        uid = str(uuid.uuid4())
        tb = traceback.format_exc()
        self.logger.write.error(json.dumps({'id': uid, 'type': 'Exception', 'method': request.method, 'status': t_error, 'addr': request.remote_addr,
                                'scheme': request.scheme, 'full_path': request.full_path, 'error': str(e), 'trace': tb}))
        return e.status_code

    def html_error(self, content):
        try:
            with open(self.__path_html_error, 'r') as f:
                template = f.read()
                f.close()
                return template.replace('{ERROR}', content)
        except Exception:
            print('Cannot get html error')
            return ''

    def init_naas_folder(self):
        try:
            os.makedirs(self.__path_naas_files)
            print('Create brain')
        except Exception:
            print('No need to create brain')
        os.system(f'chown -R ftp {self.__path_naas_files}')

    def send_response(self, uid, res, t_notebook, duration, params):
        next_url = params.get('next_url', None)
        if next_url is not None:
            if "http" not in next_url:
                next_url = f'{self.__api_internal}{next_url}'
            self.logger.write.info(json.dumps(
                {'id': uid, 'type': t_notebook, 'status': 'next_url', 'url': next_url}))
            return redirect(next_url, code=302)
        else:
            res_data = self.get_res_nb(res)
            if res_data and res_data.get('type') == 'application/json':
                return jsonify(res_data.get('data')), 200
            elif res_data:
                return Response(res_data.get('data'), mimetype=res_data.get('type'))
            else:
                return jsonify({'id': uid, "status": "Done", "time": duration}), 200


    def is_running(self, uid, notebook_filepath, target_type):
        cur_job = self.jobs.find_by_path(uid, notebook_filepath, target_type)
        if len(cur_job) == 1:
            status = cur_job[0].get('status', None)
            if (status and status == t_start):
                return True
        return False


    def scheduler_greenlet(self, main_uid, current_time, task):
        value = task.get('value', None)
        current_type = task.get('type', None)
        file_filepath = task.get('path')
        params = task.get('params', dict())
        uid = str(uuid.uuid4())
        running = self.is_running(uid, file_filepath, current_type)
        if current_type == t_scheduler and value is not None and pycron.is_now(value, current_time) and not running:
            self.logger.write.info(json.dumps(
                {'main_id': str(main_uid), 'id': uid, 'type': t_scheduler, 'status': t_start, 'filepath': file_filepath}))
            self.jobs.update(file_filepath, t_scheduler, value, params, t_start, uid)
            res = self.exec_job(uid, task)
            if (res.get('error')):
                self.logger.write.error(json.dumps({'main_id': str(main_uid), 'id': uid, 'type': t_scheduler, 'status': t_error,
                                        'filepath': file_filepath, 'duration': res.get('duration'), 'error': str(res.get('error'))}))
                self.jobs.update(file_filepath, t_scheduler, value,
                            params, t_error, uid, res.get('duration'))
                return
            self.logger.write.info(json.dumps(
                {'main_id': str(main_uid), 'id': uid, 'type': t_scheduler, 'status': t_health, 'filepath': file_filepath, 'duration': res.get('duration')}))
            self.jobs.update(file_filepath, t_scheduler, value, params,
                        t_health, uid, res.get('duration'))


    def scheduler_function(self):
        # Create unique for scheduling step (one step every minute)
        main_uid = str(uuid.uuid4())
        try:
            current_time = datetime.datetime.now()
            all_start_time = time.time()
            greelets = []
            # Write self.scheduler init info in self.logger.write
            self.logger.write.info(json.dumps({'id': main_uid, 'type': t_scheduler,
                                    'status': t_start}))
            if os.path.exists(self.__tasks_files_path):
                for task in  self.jobs.get(main_uid):
                    g = gevent.spawn(self.scheduler_greenlet,
                                    main_uid, current_time, task)
                    greelets.append(g)
                gevent.joinall(greelets)
            else:
                self.logger.write.error(json.dumps({'id': main_uid, 'type': t_scheduler, 'status': t_error,
                                        "error": '__tasks_files_path', 'path': self.__tasks_files_path}))
            durationTotal = (time.time() - all_start_time)
            self.logger.write.info(json.dumps({'id': main_uid, 'type': t_scheduler, 'status': t_health,
                                    'version': self.version(), 'duration': durationTotal}))
        except Exception as e:
            tb = traceback.format_exc()
            durationTotal = (time.time() - all_start_time)
            self.logger.write.error(json.dumps({'id': main_uid, 'type': t_scheduler, 'status': t_error,
                                    'duration': durationTotal, 'error': str(e), 'trace': tb}))
        except:
            tb = traceback.format_exc()
            durationTotal = (time.time() - all_start_time)
            self.logger.write.error(json.dumps({'id': main_uid, 'type': t_scheduler, 'status': t_error,
                                    'duration': durationTotal, 'error': str(sys.exc_info()[0]), 'trace': tb}))


    @app.before_first_request
    def init_scheduler(self):
        self.scheduler.add_job(func=self.scheduler_function,
                        trigger="interval", seconds=60, max_instances=10)
        self.scheduler.start()
        atexit.register(lambda: self.scheduler.shutdown())

    @app.route(f'/{__version_API}/')
    def statusRun(self):
        return jsonify({'status': t_health}), 200
    
    @app.route(f'/{__version_API}/env')
    def res_env(self):
        env = {
            'JUPYTERHUB_USER': os.environ.get('JUPYTERHUB_USER', ''),
            'PUBLIC_DATASCIENCE': os.environ.get('PUBLIC_DATASCIENCE', ''),
            'PUBLIC_PROXY_API': os.environ.get('PUBLIC_PROXY_API', ''),
            'TZ': os.environ.get('TZ', '')
        }
        return jsonify(env), 200

    @app.route(f'/{__version_API}/scheduler/<string:mode>')
    def mode_scheduler(self, mode):
        if (mode == 'pause'):
            self.scheduler.pause()
        elif (mode != 'status'):
            self.scheduler.resume()
        status = 'ok'
        if (self.scheduler.state == apscheduler.schedulers.base.STATE_STOPPED):
            status = 'stopped'
        elif (self.scheduler.state == apscheduler.schedulers.base.STATE_RUNNING):
            status = 'running'
        elif (self.scheduler.state == apscheduler.schedulers.base.STATE_PAUSED):
            status = 'paused'
        return jsonify({"status": status}), 200
    
    @app.route(f'/{__version_API}/logs')
    def res_logs(self):
        as_file = request.args.get('as_file', False)
        if as_file:
            res = send_file(self.logger.get_file_path(), attachment_filename='logs.csv')
            return res           
        else:
            uid = str(uuid.uuid4())
            limit = int(request.args.get('limit', 0))
            skip = int(request.args.get('skip', 0))
            search = str(request.args.get('search', ''))
            clean_logs = bool(request.args.get('clean_logs', False))
            logs = self.logger.get(uid, skip, limit, search, clean_logs)
            self.logger.write.info(json.dumps(
                {'id': uid, 'type': t_static, 'status': 'send', 'filepath': 'logs', 'skip': skip, 'limit': limit, 'search': search, 'clean_logs': clean_logs}))
            return jsonify(logs), 200

    @app.route(f'/{__version_API}/jobs', methods=['GET'])
    def res_status(self):
        uid = str(uuid.uuid4())
        status = self.jobs.get(uid)
        self.logger.write.info(json.dumps(
            {'id': uid, 'type': t_static, 'status': 'send', 'filepath': 'status'}))
        return jsonify(status), 200
    
    @app.route(f'/{__version_API}/jobs', methods=['POST'])
    def res_tasks(self):
        uid = str(uuid.uuid4())
        data = request.get_json()
        if not request.is_json:
            self.logger.write.info(json.dumps(
                {'id': uid, 'type': t_task, 'status': t_error, 'error': 'not json'}))
            return jsonify({'result': 'not json'}), 400
        if not data or ["path", "type", "params", "value", "status"].sort() != list(data.keys()).sort():
            self.logger.write.info(json.dumps(
                {'id': uid, 'type': t_task, 'status': t_error, 'error': 'missing keys', 'tb': data}))
            return jsonify({'result': 'missing keys', }), 400
        updated = self.jobs.update(
            data['path'], data['type'], data['value'], data['params'], data['status'], uid)
        self.logger.write.info(json.dumps(
            {'id': uid, 'type': t_task, 'status': updated['status']}))
        return jsonify(updated), 200

    @app.route(f'/{__version_API}/manager')
    def res_manager(self):
        uid = str(uuid.uuid4())
        self.logger.write.info(json.dumps(
            {'id': uid, 'type': t_static, 'status': 'send', 'filepath': self.__path_manager_index}))
        return send_file(self.__path_manager_index), 200

    @app.route(f'/{__version_API}/{t_static}/up')
    def resUp(self):
        file_filename = 'up.png'
        file_filepath = os.path.join(self.__path_lib_files, self.__assets_files, file_filename)
        try:
            res = send_file(file_filepath, attachment_filename=file_filename)
            return res
        except Exception as e:
            return self.html_error(json.dumps({"error": e})), 404
        
    @app.route(f'/{__version_API}/{t_static}/down')
    def resDown(self, token):
        file_filename = 'down.png'
        file_filepath = os.path.join(self.__path_lib_files, self.__assets_files, file_filename)
        try:
            res = send_file(file_filepath, attachment_filename=file_filename)
            return res
        except Exception as e:
            return self.html_error(json.dumps({"error": e})), 404
        
    @app.route(f'/{__version_API}/{t_static}/<string:token>')
    def resStatic(self, token):
        uid = str(uuid.uuid4())
        task = self.jobs.find_by_value(uid, token, t_static)
        if task:
            file_filepath = task.get('path')
            file_filename = os.path.basename(file_filepath)
            params = task.get('params', dict())
            self.logger.write.info(json.dumps(
                {'id': uid, 'type': t_static, 'status': t_start, 'filepath': file_filepath, 'token': token}))
            try:
                self.jobs.update(file_filepath, t_static, token,
                            params, t_health, uid, 1)
                res = send_file(file_filepath, attachment_filename=file_filename)
                self.logger.write.info(json.dumps(
                    {'id': uid, 'type': t_static, 'status': t_start, 'filepath': file_filepath, 'token': token}))
                return res
            except Exception as e:
                self.logger.write.error(json.dumps(
                    {'id': uid, 'type': t_static, 'status': t_error, 'filepath': file_filepath, 'token': token, "error": e}))
                self.jobs.update(file_filepath, t_static,
                            token, params, t_error, uid, 1)
                return self.html_error(json.dumps({'id': uid, "error": e})), 404
        self.logger.write.error(json.dumps({'id': uid, 'type': t_static, 'status': t_error,
                                "error": 'Cannot find your token', 'token': token}))
        return self.html_error(json.dumps({'id': uid, "error": "Cannot find your token", 'token': token})), 401


    @app.route(f'/{__version_API}/{t_notebook}/<string:token>')
    def startNotebook(self, token):
        uid = str(uuid.uuid4())
        task = self.jobs.find_by_value(uid, token, t_notebook)
        if task:
            value = task.get('value', None)
            file_filepath = task.get('path')
            task['params'] = {**(task.get('params', dict())), **(request.args)}
            self.logger.write.info(json.dumps(
                {'id': uid, 'type': t_notebook, 'status': t_start, 'filepath': file_filepath, 'token': token}))
            res = self.exec_job(uid, task)
            if (res.get('error')):
                self.logger.write.error(json.dumps({'main_id': uid, 'id': uid, 'type': t_notebook, 'status': t_error,
                                        'filepath': file_filepath, 'duration': res.get('duration'), 'error': res.get('error')}))
                self.jobs.update(file_filepath, t_notebook, value, task.get(
                    'params'), t_error, uid, res.get('duration'))
                return jsonify({'id': uid, "error": res.get('error')}), 200
            self.logger.write.info(json.dumps(
                {'main_id': uid, 'id': uid, 'type': t_notebook, 'status': t_health, 'filepath': file_filepath, 'duration': res.get('duration')}))
            self.jobs.update(file_filepath, t_notebook, value, task.get(
                'params'), t_health, uid, res.get('duration'))
            return self.send_response(uid, res, t_notebook, res.get('duration'), task.get('params'))
        self.logger.write.error(json.dumps({'id': uid, 'type': t_notebook, 'status': t_error,
                                'token': token, 'error': 'Cannot find your token'}))
        return jsonify({'id': uid, "error": "Cannot find your token"}), 401
