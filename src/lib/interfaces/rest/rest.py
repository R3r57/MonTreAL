import logging, os, threading
from flask import Flask
from flask_restful import Resource, Api
from lib.interfaces.memcache.client import Client
from multiprocessing import Process

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class Rest(threading.Thread):
    def __init__(self, name, event, config):
        super(Rest, self).__init__()
        self.name = name
        self.event = event
        self.app = Flask(__name__)
        self.app.use_relader = False
        api = Api(self.app)
        api.add_resource(SensorData,
                         '/<string:prefix>/<string:machine_id>/<string:sensor_id>',
                         resource_class_kwargs={"memcache_client": Client(config)})
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started {}".format(self.name))
        server = Process(target=self.app.run, kwargs={"host": "0.0.0.0", "debug": True})
        server.start()
        self.event.wait()
        server.terminate()
        server.join(15)
        logger.info("Stopped {}".format(self.name))

class SensorData(Resource):
    def __init__(self, memcache_client):
        Resource.__init__(self)
        self.memcache_client = memcache_client

    def get(self, prefix, machine_id, sensor_id):
        data = self.memcache_client.read("{}{}{}".format(str(prefix), str(machine_id), str(sensor_id)))
        return data
