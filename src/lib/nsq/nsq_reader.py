import os, logging, threading, gnsq
from multiprocessing import Queue
from multiprocessing import Process

logger = logging.LoggerAdapter(logging.getLogger(), {"class": os.path.basename(__file__)})

class NsqReader (threading.Thread):
    def __init__(self, name, event, queue, config, channel="default"):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.config = config
        self.queue = queue
        if ("name" not in self.config["nsqlookupd"]):
            nsqld_ip = self.config["nsqlookupd"]['ip']
            self.config["nsqlookupd"]["name"] = (nsqld_ip.split('://'))[1]
        if ("name" not in self.config["nsqd"]):
            nsqd_ip = self.config["nsqd"]['ip']
            self.config["nsqd"]["name"] = (nsqd_ip.split('://'))[1]
        url = "{}:{}".format(self.config["nsqlookupd"]["name"],
                             self.config["nsqlookupd"]["port"])
        intervall = self.config["nsqlookupd"]["interval"]
        self.reader = gnsq.Reader(message_handler=self.message_handler,
                                  lookupd_http_addresses=url,
                                  lookupd_poll_interval=intervall,
                                  topic=self.config["topics"]["data_topic"],
                                  channel=channel)

        self.writer = gnsq.Nsqd(address=self.config["nsqd"]["name"],
                                http_port=self.config["nsqd"]["port"])
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started: {}".format(self.name))
        server = Process(target=self.reader.start)
        try:
            logger.info("Creating topic (if not exists): {}".format(self.config["topics"]["data_topic"]))
            self.writer.create_topic(self.config["topics"]["data_topic"])
            logger.info("Starting reader process...")
            server.start()
            self.event.wait(2)
            logger.info("...success")
            while not self.event.is_set():
                self.event.wait()
        except Exception as e:
            logger.error("{}".format(e))
        finally:
            self.reader.close()
            self.reader.join(10)
            server.terminate()
            server.join(15)
            logger.info("Stopped: {}".format(self.name))

    def message_handler(self, nsqr, message):
        logger.info("NSQ message received")
        data = message.body.decode()
        self.queue.put(str(data))
        logger.info("Data put into queue: {}".format(str(data)))
