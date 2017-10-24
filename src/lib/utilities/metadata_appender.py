import logging, threading, json, os
from queue import Queue
from lib.utilities.data import SensorData

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class MetaDataAppender(threading.Thread):

    def __init__(self, name, event, input_queue, output_queue, config):
        super(MetaDataAppender, self).__init__()
        self.name = name
        self.event = event
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.hostname = None
        self.machine_id = None
        self.building = None
        self.room = None
        self.__init_metadata(config)
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started {}".format(self.name))
        while not self.event.is_set():
            self.event.wait(2)

            while not self.input_queue.empty():
                raw = self.input_queue.get()
                logger.info("Raw data received")
                deserialized_data = json.loads(raw.replace("'", '"'))
                converted_data = self.__convert(deserialized_data)
                serialized_data = converted_data.to_json()
                self.output_queue.put(serialized_data)
                self.input_queue.task_done()
                logger.info("Data put in queue")
        logger.info("Stopped: {}".format(self.name))

    def __init_metadata(self, config):
        tmp = self.__get_file_content(config["hostname_path"])
        self.hostname = tmp[0].split("\n")[0]
        tmp2 = self.__get_file_content(config["machine_id_path"])
        self.machine_id = tmp2[0].split("\n")[0]
        location_info = self.__get_file_content(config["location_info_path"])
        self.building = location_info[0].split("=")[1].split("\n")[0]
        self.room = location_info[1].split("=")[1].split("\n")[0]
        logger.info("Configuration: {}, {}, {}, {}".format(self.hostname, self.machine_id, self.building, self.room))

    def __get_file_content(self, filepath):
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                metadata = f.readlines()
            return metadata
        elif os.path.exists:
            logger.error("File doesn't exist: {}".format(filepath))
        return None

    def __convert(self, data):
        return SensorData(self.hostname,
                          self.machine_id,
                          self.building,
                          self.room,
                          data)
