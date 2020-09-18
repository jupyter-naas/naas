from sanic.views import HTTPMethodView
from sanic.response import json
from naas.types import t_static
import uuid

class JobsController(HTTPMethodView):
    __jobs = None
    __logger = None
    
    def __init__(self, logger, jobs, *args, **kwargs):
        super(JobsController, self).__init__(*args, **kwargs)
        self.__jobs = jobs
        self.__logger = logger
    
    async def get(self, request):
        uid = str(uuid.uuid4())
        status = self.__jobs.list(uid)
        self.__logger.info(
            {'id': uid, 'type': t_static, 'status': 'send', 'filepath': 'status'})
        return json(status)
    
    async def post(self, request):
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
        return json(updated)