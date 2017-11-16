import json
import logging
import os
import threading

from influxdb import client as influxdb
from lib.interfaces.influxdb.influxdb_converter import InfluxDBConverter


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class InfluxDBWriter(threading.Thread):
    def __init__(self, name, event, queue, config):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.config = config
        self.converter = InfluxDBConverter(self.config['measurements'])
        self.influxdb = influxdb.InfluxDBClient(self.config['ip'], self.config['port'], self.config['user'], self.config['password'], self.config['database'])
        self.influxdb.create_database(self.config['database'])
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started {}".format(self.name))
        while not self.event.is_set():
            self.event.wait(1)
            while not self.queue.empty():
                data = json.loads(self.queue.get())
                influxdb_format = self.converter.convert(data)
                self.__send_data(influxdb_format.get())
                logger.info("Received data from queue and put into Influxdb")
        logger.info("Stopped {}".format(self.name))

    def __send_data(self, line):
        self.influxdb.write_points(line)
