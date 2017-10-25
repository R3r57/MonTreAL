import os, gnsq, logging, threading
from queue import Queue

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class NsqWriter (threading.Thread):
    def __init__(self, name, event, queue, config):
        threading.Thread.__init__(self)
        self.name = name
        self.config = config
        self.event = event
        self.queue = queue
        self.timeout = int(self.config["connection"]["timeout"])
        self.max_tries = int(self.config["connection"]["max_tries"])

        nsqlookup_url = "{}:{}".format(self.config["nsqlookupd"]["ip"],
                self.config["nsqlookupd"]["port"])

        self.writer = gnsq.Nsqd(address=self.config["nsqd"]["ip"],
                http_port=self.config["nsqd"]["port"])

        self.lookup = gnsq.Lookupd(address=nsqlookup_url)

        logger.info("{} initialized successfully".format(self.name))

    def __check_connection(self):
        counter = 1
        while True:
            logger.info("Trying to connect to NSQ ({}/{})".format(str(counter), str(self.max_tries)))
            try:
                ping_nsq = (self.writer.ping()).decode()
                ping_lookup = (self.lookup.ping()).decode()
                logger.info("NSQD [{}] - NSQLOOKUPD [{}]".format(ping_nsq, ping_lookup))
                if "OK" in ping_nsq and "OK" in ping_lookup:
                    return True
            except Exception as e:
                if counter < self.max_tries:
                    counter += 1
                    self.event.wait(self.timeout)
                else:
                    logger.error("NSQD or NSQLOOKUP not found")
                    return False

    def run(self):
        logger.info("Started {}".format(self.name))
        if not self.__check_connection():
           self.event.set()

        while not self.event.is_set():
            self.event.wait(1)
            while not self.queue.empty():
                data = self.queue.get()
                self.__send(data)
                logger.info("Received data from queue and put into NSQ")
        logger.info("Stopped {}".format(self.name))

    def __send(self, data):
        if self.__check_connection():
            self.writer.publish(self.config["topics"]["data_topic"], data)
