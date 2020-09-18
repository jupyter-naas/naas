from sanic.views import HTTPMethodView
from sanic import response
from naas.types import t_static, t_notebook, t_health, t_error
import uuid
import json
import os

class StaticController(HTTPMethodView):
    __logger = None
    __jobs = None
    __path_lib_files = None
    __path_html_error = None
    __assets_files = 'assets'
    __html_files = 'html'
    __manager_error = 'error.html'
    
    def __init__(self, logger, jobs, path_assets, *args, **kwargs):
        super(StaticController, self).__init__(*args, **kwargs)
        self.__logger = logger
        self.__jobs = jobs
        self.__path_lib_files = path_assets
        self.__path_html_error = os.path.join(self.__path_lib_files, self.__html_files, self.__manager_error)
        print('self.__path_html_error', self.__path_html_error)

    def __html_error(self, content):
        try:
            with open(self.__path_html_error, 'r') as f:
                template = f.read()
                f.close()
                return template.replace('{ERROR}', content)
        except Exception:
            print('Cannot get html error')
            return ''

    def get(self, request, token):
        path = None 
        if (token == 'up' or token == 'down'):
            return response.file(os.path.join(self.__path_lib_files, self.__assets_files, f"{token}.png"))
        else:
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
                    res = response.file(file_filepath, attachment_filename=file_filename)
                    self.__logger.info(
                        {'id': uid, 'type': t_static, 'status': t_start, 'filepath': file_filepath, 'token': token})
                    return res
                except Exception as e:
                    self.__logger.error(
                        {'id': uid, 'type': t_static, 'status': t_error, 'filepath': file_filepath, 'token': token, "error": e})
                    self.__jobs.update(uid, file_filepath, t_static,
                                token, params, t_error, 1)
                    return response.html(self.__html_error(json.dumps({'id': uid, "error": e})))
            self.__logger.error({'id': uid, 'type': t_static, 'status': t_error,
                                    "error": 'Cannot find your token', 'token': token})
            return response.html(self.__html_error(json.dumps({'id': uid, "error": "Cannot find your token", 'token': token})))


