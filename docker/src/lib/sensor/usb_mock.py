import threading
import json


class USBmock (threading.Thread):
    def __init__(self, name, event, queue):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.counter = 0
        self.message = {"hostname": "UB-Magazin",
                        "machine_id": "12345",
                        "room": "UB/00.08",
                        "library": "TB3",
                        "sensor_id": 0,
                        "measures": [
                                    {"name": "temperature",
                                     "value": 25.3, "unit": "°C"},
                                    {"name": "humidity",
                                     "value": 50, "unit": "%"}]}

    def run(self):
        print("Starting " + self.name)
        while not self.event.is_set():
            if self.queue.empty():
                print("new measure: {}".format(self.counter))
                self.queue.put(str(self.message))
                self.message["sensor_id"] += 1
                self.counter += 1
            if self.counter % 20 == 0:
                self.message["sensor_id"] = 0
            self.event.wait(10)
        print("stop", self.name)
