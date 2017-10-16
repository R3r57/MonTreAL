from flask import Flask
from flask_restful import Resource, Api
from lib.prtg.memcached import Memcached
import threading
from multiprocessing import Process


class PRTGweb (threading.Thread):
    def __init__(self, name, event, config):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.app = Flask(__name__)
        self.app.use_reloader = False
        api = Api(self.app)
        api.add_resource(Sensors,
                         '/<string:prefix>/<string:device_id>/<string:sensor_id>',
                         resource_class_kwargs={"memcached": Memcached(config)})

    def run(self):
        server = Process(target=self.app.run, kwargs={"host": "0.0.0.0",
                                                      "debug": False})
        server.start()
        self.event.wait()
        server.terminate()
        server.join(15)


class Sensors(Resource):
    def __init__(self, memcached):
        Resource.__init__(self)
        self.memcached = memcached

    def get(self, prefix, device_id, sensor_id):
        data = self.memcached.read("{}{}{}".format(str(prefix),
                                                   str(device_id),
                                                   str(sensor_id)))
        print(data)
        return data
