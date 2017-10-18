from lib.prtg.memcached import Memcached
import threading
import json
from multiprocessing import Queue


class RawMem (threading.Thread):
    def __init__(self, name, event, queue, config, prefix="json"):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.prefix = prefix
        self.memcached = Memcached(config)

    def run(self):
        print("Starting " + self.name)

        while not self.event.is_set():
            self.event.wait(2)

            while not self.queue.empty():
                data = json.loads(self.queue.get().replace("'", '"'))
                print("write raw to memcached")
                #: {}".format(data))
                keyvalue = "{}{}_{}{}".format(self.prefix,
                                              data["hostname"],
                                              data["machine_id"],
                                              str(data["sensor_id"]))
                self.memcached.write(keyvalue, data)
        print("stop", self.name)
