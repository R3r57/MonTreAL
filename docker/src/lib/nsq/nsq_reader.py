import threading
import gnsq
from multiprocessing import Queue
from multiprocessing import Process


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

    def run(self):
        server = Process(target=self.reader.start)
        try:
            #create topic if it doesn't exist
            print("Create topic if it doesn't exist")
            self.writer.create_topic(self.config["topics"]["data_topic"])
            print("Starting " + self.name)
            server.start()
            self.event.wait(2)
            print(self.name + " started")
            while not self.event.is_set():
                self.event.wait()
        except Exception as e:
            print("Error! Shutting down\n", e)
        finally:
            self.reader.close()
            self.reader.join(10)
            server.terminate()
            server.join(15)

    def message_handler(self, nsqr, message):
        data = message.body.decode()
        print("receive nsq message")
        self.queue.put(str(data))
