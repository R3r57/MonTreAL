import logging
import os
import threading
import gnsq

from multiprocessing import Process, Queue


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class NsqReader (threading.Thread):
    def __init__(self, name, event, queue, config, channel="default"):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.config = config
        self.queue = queue
        self.timeout = int(self.config["connection"]["timeout"])
        self.max_tries = int(self.config["connection"]["max_tries"])

        nsqlookup_url = "{}:{}".format(self.config["nsqlookupd"]["ip"],
                self.config["nsqlookupd"]["port"])

        self.reader = gnsq.Reader(message_handler=self.message_handler,
                lookupd_http_addresses=nsqlookup_url,
                lookupd_poll_interval=self.config["nsqlookupd"]["interval"],
                topic=self.config["topics"]["data_topic"],
                channel=channel)

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
        logger.info("Started: {}".format(self.name))
        try:
            process = Process(target=self.reader.start)
            if not self.__check_connection():
                self.event.set()
            else:
                self.writer.create_topic(self.config["topics"]["data_topic"])
            while not self.event.is_set():
                if not process.is_alive():
                    logger.info("Subprocess for reader not alive...starting")
                    process.start()
                self.event.wait(2)
        except Exception as e:
            logger.error("{}".format(e))
        finally:
            self.reader.close()
            self.reader.join(5)
            process.terminate()
            process.join(5)
            logger.info("Stopped: {}".format(self.name))

    def message_handler(self, nsqr, message):
        logger.info("NSQ message received and put in queue")
        data = message.body.decode()
        self.queue.put(str(data))
