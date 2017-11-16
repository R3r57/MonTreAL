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
                         '/<string:prefix>/<string:device_id>/<string:sensor>/<string:sensor_id>',
                         resource_class_kwargs={"memcache_client": Client(config)})
        api.add_resource(SensorList,
                         '/<string:prefix>/sensorlist',
                         resource_class_kwargs={"memcache_client": Client(config)})
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started {}".format(self.name))
        try:
            process = Process(target=self.app.run, kwargs={"host": "0.0.0.0", "debug": True})
            while not self.event.is_set():
                if not process.is_alive():
                    logger.info("Subprocess for REST not alive...starting")
                    process.start()
                self.event.wait(2)
        except Exception as e:
            logger.error("{}".format(e))
        finally:
            process.terminate()
            process.join(15)
            logger.info("Stopped {}".format(self.name))

class SensorData(Resource):
    def __init__(self, memcache_client):
        Resource.__init__(self)
        self.memcache_client = memcache_client

    def get(self, prefix, device_id, sensor, sensor_id):
        data = self.memcache_client.read("{}{}{}{}".format(str(prefix), str(device_id), str(sensor), str(sensor_id)))
        return data

class SensorList(Resource):
    def __init__(self, memcache_client):
        super(SensorList, self).__init__()
        self.memcache_client = memcache_client

    def get(self, prefix):
        data = self.memcache_client.read("{}sensorlist".format(prefix))
        return data
