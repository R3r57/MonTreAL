import threading
import json
import os
import pickle
from queue import Queue
from lib.sensor.sensor_data import SensorData, Measurement


class MetaDataAppender(threading.Thread):

    def __init__(self, name, event, input_queue, output_queue, config):
        super(MetaDataAppender, self).__init__()
        self.name = name
        self.event = event
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.hostname = None
        self.machine_id = None
        self.library = None
        self.room = None
        self.init_metadata(config)

    def run(self):
        while not self.event.is_set():
            self.event.wait(2)

            while not self.input_queue.empty():
                raw = self.input_queue.get()
                print("raw data")
                print(raw)
                deserialized_data = json.loads(raw.replace("'", '"'))
#                deserialized_data = pickle.loads(self.input_queue.get())
                converted_data = self.convert(deserialized_data)
                print("append data")
                print(converted_data)
                serialized_data = converted_data.to_json()
                self.output_queue.put(serialized_data)
                self.input_queue.task_done()

    def init_metadata(self, config):
        tmp = self.get_file_content(config["hostname_path"])
        self.hostname = tmp[0].split("\n")[0]
        tmp2 = self.get_file_content(config["machine_id_path"])
        self.machine_id = tmp2[0].split("\n")[0]
        location_info = self.get_file_content(config["location_info_path"])
        self.library = location_info[0].split("=")[1].split("\n")[0]
        self.room = location_info[1].split("=")[1].split("\n")[0]

    def get_file_content(self, filepath):
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                metadata = f.readlines()
            return metadata
        elif os.path.exists:
            print("path exists but is not a file {}", filepath)
        return None

    def convert(self, data):
        return SensorData(self.hostname,
                          self.machine_id,
                          self.room,
                          self.library, data)
