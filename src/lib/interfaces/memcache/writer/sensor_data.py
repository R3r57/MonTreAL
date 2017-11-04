from lib.interfaces.memcache.client import Client
import threading, json, logging, os

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class SensorDataWriter (threading.Thread):
    def __init__(self, name, event, queue, config, prefix="json"):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.prefix = prefix
        self.memcached = Client(config)
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started: {}".format(self.name))
        while not self.event.is_set():
            self.event.wait(2)
            while not self.queue.empty():
                data = json.loads(self.queue.get().replace("'", '"'))
                keyvalue = "{}{}{}".format(self.prefix,
                                              data["machine_id"],
                                              str(data["sensor_id"]))
                self.memcached.write(keyvalue, data)
                logger.info("Wrote data into memcache: {}".format(keyvalue))
        logger.info("Stopped: {}".format(self.name))
