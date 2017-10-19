import logging, os, threading, json
from lib.sensor.sensor_type.data import Measurement

logger = logging.LoggerAdapter(logging.getLogger(), {"class": os.path.basename(__file__)})

class SensorMock (threading.Thread):
    def __init__(self, name, event, queue):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.counter = 1
        logger.info("{} initialized successfully".format(self.name))
        
    def run(self):
        logger.info("Started: {}".format(self.name))
        while not self.event.is_set():
            if self.queue.empty():
                logger.info("Putting data in queue...")
                measurement = Measurement(self.counter, 23.0, 56.0).to_json()
                self.queue.put(json.dumps(measurement))
                self.counter = self.counter + 1
                logger.info("...success")
                if self.counter >= 5:
                    self.counter = 1
            self.event.wait(10)
        logger.info("Stopped: {}".format(self.name))
