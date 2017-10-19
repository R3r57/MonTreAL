import os
import gnsq
import logging
import threading
from queue import Queue

logger = logging.LoggerAdapter(logging.getLogger(), {"class": os.path.basename(__file__)})

class NsqWriter (threading.Thread):
    def __init__(self, name, event, queue, config):
        threading.Thread.__init__(self)
        self.name = name
        self.config = config
        self.event = event
        self.queue = queue
        if ("name" not in self.config["nsqd"]):
            nsqd_ip = self.config["nsqd"]['ip']
            self.config["nsqd"]["name"] = (nsqd_ip.split('://'))[1]
        self.writer = gnsq.Nsqd(address=self.config["nsqd"]["name"],
                                http_port=self.config["nsqd"]["port"])
        if ("writer" not in self.config["nsqd"]):
            self.config["nsqd"]["writer"] = { "timeout": 10,
                                              "max_tries": 10 }
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started {}".format(self.name))
        bLoop = True
        bError = False
        iCounter = 0

        while bLoop:
            logger.info("Trying to connect to NSQ...")
            iCounter += 1
            try:
                ping = (self.writer.ping()).decode()
                if "OK" in ping:
                    bLoop = False
                    logger.info("...success")
            except:
                if iCounter >= 10:
                    bError = True
                    bLoop = False
                    logger.info("...failed")
                else:
                    logger.info("...retrying...")
                    self.event.wait(int(self.config["writer"]["timeout"]))
            if bError:
                logger.error("Could not connect to NSQ")
                return

        while not self.event.is_set():
            self.event.wait(1)
            while not self.queue.empty():
                logger.info("Getting data from queue...")
                data = self.queue.get()
                self.queue.task_done()
                logger.info("...received and put into queue")
                self.send(data)
        logger.info("Stopped {}".format(self.name))

    def send(self, data):
        self.writer.publish(self.config["topics"]["data_topic"], data)
