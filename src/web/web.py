import logging
import os
import threading

from multiprocessing import Process
from flask import Flask
from flask_restful import Api, Resource
from memcache.meta.client import Client

from web.resources.sensor_data import SensorData
from web.resources.sensor_list import SensorList


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class Web(threading.Thread):
    def __init__(self, name, event, config):
        super(Web, self).__init__()
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
                    logger.info("Subprocess for Web not alive...starting")
                    process.start()
                self.event.wait(2)
        except Exception as e:
            logger.error("{}".format(e))
        finally:
            process.terminate()
            process.join(15)
            logger.info("Stopped {}".format(self.name))
