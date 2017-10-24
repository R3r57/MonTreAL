import os, logging
from lib.sensors.ash2200 import ASH2200
from lib.sensors.sensor_mock import SensorMock
from lib.interfaces.socket.socket_writer import SocketWriter
from lib.interfaces.socket.socket_reader import SocketReader
from lib.interfaces.nsq.nsq_writer import NsqWriter
from lib.interfaces.nsq.nsq_reader import NsqReader
from lib.interfaces.memcache.writer.raw import RawWriter
from lib.utilities.metadata_appender import MetaDataAppender
from lib.utilities.local_container import LocalContainer
from queue import Queue

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class Services:

    def __init__(self, config, event):
        self.config = config
        self.event = event
        self.services = {
            "sensor": self.__create_sensors,
            "local_manager": self.__create_local_manager,
            "raw_memcache_writer": self.__create_raw_memcache
        }

    def get_services(self, type):
        return self.services.get(type)()

##################################################################
# Local Manager                                                  #
##################################################################
    def __create_local_manager(self):
            threads = []

            message_queue = Queue(maxsize=10)
            socket_reader = SocketReader("SocketReader", self.event, message_queue)
            threads.append(socket_reader)

            meta_queue = Queue(maxsize=10)
            meta_data_appender = MetaDataAppender("MetaData", self.event, message_queue, meta_queue, self.config['utilities']['metadata'])
            threads.append(meta_data_appender)

            nsq_writer = NsqWriter("NsqWriter", self.event, meta_queue, self.config['interfaces']['nsq'])
            threads.append(nsq_writer)

            local_container = LocalContainer("LocalContainer", self.event, {"local": self.config['utilities']['local'], "sensors": self.config['sensors']})
            threads.append(local_container)

            return threads

##################################################################
# Local Sensor                                                   #
##################################################################
    def __create_sensors(self):
            threads = []
            type = os.environ['TYPE']

            sensor_queue = Queue()

            if type == "ash2200":
                usb_serial = USBSerial("/dev/ttyUSB-1", 9599, 19)
                ash2200 = ASH2200("USB", usb_serial, self.event, sensor_queue)
                threads.append(usb_serial, ash2200)
            elif type == "mock":
                mock = SensorMock("Mock", self.event, sensor_queue)
                threads.append(mock)
            else:
                logger.error("No sensortype selected: {}".format(type))

            socket_writer = SocketWriter("SocketWriter", self.event, sensor_queue, os.environ['SOCKET'])
            threads.append(socket_writer)

            return threads

##################################################################
# Raw Memcache                                                   #
##################################################################
    def __create_raw_memcache(self):
            threads = []

            queue = Queue(maxsize=10)
            nsq_reader = NsqReader("Raw_Memcache_NsqReader", self.event, queue, self.config['interfaces']['nsq'], channel="memcache_raw")
            threads.append(nsq_reader)

            raw_memcache_writer = RawWriter("Raw_Memcache_Writer", self.event, queue, self.config['interfaces']['memcached'])
            threads.append(raw_memcache_writer)

            return threads
