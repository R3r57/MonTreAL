import json
import logging
import os
import random
import threading

from sensors.data import Measurement


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
        message_counter = 1
        while not self.event.is_set():
            if self.queue.empty():
                for sensor_id in range(1, self.sensor_count + 1):
                    temp_derivation = random.randint(-2, 2)
                    hum_derivation = random.randint(-5, 5)
                    logger.info("Measurement {} put into queue".format(message_counter))
                    measurement = Measurement(sensor_id, "SensorMock", (self.temp + temp_derivation), (self.hum + hum_derivation)).to_json()
                    self.queue.put(json.dumps(measurement))
                    message_counter += 1
            self.event.wait(self.interval)
        logger.info("Stopped: {}".format(self.name))
