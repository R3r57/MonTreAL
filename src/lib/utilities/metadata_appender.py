import logging, threading, json, os
from queue import Queue
from lib.utilities.data import SensorData

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class MetaDataAppender(threading.Thread):

    def __init__(self, name, event, input_queue, output_queue, config):
        super(MetaDataAppender, self).__init__()
        self.name = name
        self.event = event
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.hostname = None
        self.machine_id = None
        self.building = None
        self.room = None
        self.__init_metadata()
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
                logger.info("Data put in queue")
        logger.info("Stopped: {}".format(self.name))

    def __init_metadata(self):
        local_configuration = self.__get_local_configuration()
        self.hostname = self.__get_hostname(local_configuration['hostname'])
        self.machine_id = local_configuration['machine_id']
        self.building = local_configuration['building']
        self.room = local_configuration['room']

    def __get_hostname(self, path):
        if os.path.isfile(path):
            with open(path) as file:
                return file.readline().strip()
        else:
            logger.error("Unable to locate {} for hostname".format(path))
            return "unspecified"

    def __get_local_configuration(self):
        local_configuration_path = self.config['local_configuration']
        logger.info("Local configuration file set to {}".format(local_configuration_path))
        if os.path.isfile(local_configuration_path):
            with open(local_configuration_path, 'r') as file:
                data = json.load(file)
                return data
        else:
            logger.error("Local configuration file not found: {}".format(local_configuration_path))

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
