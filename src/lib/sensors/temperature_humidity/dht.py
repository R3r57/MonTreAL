import json
import logging
import os
import threading
import Adafruit_DHT

from lib.sensors.data import Measurement

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class DHT(threading.Thread):

    def __init__(self, name, config, event, queue):
        threading.Thread.__init__(self)
        self.name = name
        self.id = config['id']
        self.gpio = config['gpio']
        self.short_type = config['short_type']
        self.interval = config['interval']
        self.type = "DHT{}".format(self.short_type)
        self.queue = queue
        self.event = event
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started: {}".format(self.name))
        while not self.event.is_set():
            try:
                logger.info("Reading data from GPIO...")
                hum, temp = Adafruit_DHT.read_retry(sensor=self.short_type, pin=self.gpio)
                if hum and temp:
                    data = Measurement(self.id, self.type, temp, hum).to_json()
                    logger.info("Data received: {}".format(data))
                    self.queue.put(json.dumps(data))
                    logger.info("Data put into queue")
                self.event.wait(self.interval)
            except Exception:
                raise
        logger.info("Stopped: {}".format(self.name))
