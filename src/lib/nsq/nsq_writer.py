import gnsq
import logging
import threading
from queue import Queue


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

    def run(self):
        bLoop = True
        bError = False
        iCounter = 0
        print("Starting " + self.name)

        while bLoop:
            iCounter += 1
            print("Connect to NSQ")
            try:
                ping = (self.writer.ping()).decode()
                if "OK" in ping:
                    bLoop = False
            except:
                if iCounter >= 10:
                    bError = True
                    bLoop = False
                else:
                    print("Can't connect to NSQ...\nRetrying...")
                    self.event.wait(int(self.config["writer"]["timeout"]))
            if bError:
                raise Exception("Couldn't reach NSQ")

        while not self.event.is_set():
            self.event.wait(1)
            while not self.queue.empty():
                data = self.queue.get()
                self.queue.task_done()
                print("publish in nsq")
                self.send(data)
        print("Stopping ", self.name)

    def send(self, data):
        self.writer.publish(self.config["topics"]["data_topic"], data)
