import json
import logging
import os
import threading

from queue import Queue
from lib.utilities.data import SensorData


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class MetaDataAppender(threading.Thread):

    def __init__(self, name, event, input_queue, output_queue, config):
        super(MetaDataAppender, self).__init__()
        self.name = name
        self.event = event
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.hostname = self.__get_hostname("/etc/hostname")
        self.device_id = self.config['meta']['device_id']
        self.building = self.config['location']['building']
        self.room = self.config['location']['room']
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started {}".format(self.name))
        while not self.event.is_set():
            self.event.wait(2)
            while not self.input_queue.empty():
                raw = self.input_queue.get()
                logger.info("Raw data received")
                deserialized_data = json.loads(raw.replace("'", '"'))
                converted_data = self.__convert(deserialized_data)
                serialized_data = converted_data.to_json()
                self.output_queue.put(serialized_data)
                logger.info("Data put in queue")
        logger.info("Stopped: {}".format(self.name))

    def __get_hostname(self, path):
        if os.path.isfile(path):
            with open(path) as file:
                return file.readline().strip()
        else:
            logger.error("Unable to locate {} for hostname".format(path))
            return "unspecified"

    def __convert(self, data):
        return SensorData(self.hostname,
                          self.device_id,
                          self.building,
                          self.room,
                          data)
