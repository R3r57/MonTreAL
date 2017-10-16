from lib.prtg.memcached import Memcached
from lib.prtg.prtg import PRTG
import threading
import json
from multiprocessing import Queue


class PRTGconverter (threading.Thread):
    def __init__(self, name, event, queue, config, prefix="prtg"):
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
                print("convert for prtg")
                #: {}".format(data))
                self.convert(data)
        print("stop", self.name)

    def convert(self, data):
        paessler = PRTG()
        keyvalue = "{}{}_{}{}".format(self.prefix,
                                      data["hostname"],
                                      data["machine_id"],
                                      str(data["sensor_id"]))
        paessler.set_text("{} {}".format(data["hostname"],
                                         str(data["sensor_id"])))
        for measure in data["measures"]:
            paessler.add_channel(measure["name"],
                                 measure["value"],
                                 measure["unit"])
        print(keyvalue)
        self.memcached.write(keyvalue, paessler.get_json())
