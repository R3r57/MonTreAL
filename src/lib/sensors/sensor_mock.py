import logging, os, threading, json
from lib.sensors.data import Measurement

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class SensorMock (threading.Thread):
    def __init__(self, name, event, queue, config):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.sensor_count = config['sensor_count']
        self.temp = config['temperature']
        self.hum = config['humidity']
        self.interval = config['interval']
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started: {}".format(self.name))
        sensor_id = 1
        message_counter = 1
        while not self.event.is_set():
            if self.queue.empty():
                logger.info("Measurement {} put into queue".format(message_counter))
                measurement = Measurement(sensor_id, self.temp, self.hum).to_json()
                self.queue.put(json.dumps(measurement))
                sensor_id += 1
                message_counter += 1
                if sensor_id >= self.sensor_count:
                    sensor_id = 1
            self.event.wait(self.interval)
        logger.info("Stopped: {}".format(self.name))
