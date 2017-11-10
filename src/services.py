import os, logging
from lib.interfaces.nsq.nsq_reader import NsqReader
from multiprocessing import Queue

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class Services:

    def __init__(self, config, event):
        self.config = config
        self.event = event
        self.services = {
            "sensor": self.__create_sensors,
            "local_manager": self.__create_local_manager,
            "sensor_data_memcache_writer": self.__create_sensor_data_memcache,
            "influxdb_writer": self.__create_influxdb,
            "prometheus_writer": self.__create_prometheus,
            "rest": self.__create_rest,
            "sensor_list_memcache_writer": self.__create_sensor_list_creator
        }

    def get_services(self, type):
        return self.services.get(type)()

##################################################################
# Local Manager                                                  #
##################################################################
    def __create_local_manager(self):
            from lib.interfaces.socket.socket_reader import SocketReader
            from lib.utilities.metadata_appender import MetaDataAppender
            from lib.utilities.local_container import LocalContainer
            from lib.interfaces.nsq.nsq_writer import NsqWriter
            threads = []

            message_queue = Queue(maxsize=10)
            socket_reader = SocketReader("SocketReader", self.event, message_queue)
            threads.append(socket_reader)

            meta_queue = Queue(maxsize=10)
            meta_data_appender = MetaDataAppender("MetaData", self.event, message_queue, meta_queue, self.config['utilities']['metadata'])
            threads.append(meta_data_appender)

            nsq_writer = NsqWriter("NsqWriter", self.event, meta_queue, self.config['interfaces']['nsq'])
            threads.append(nsq_writer)

            local_container = LocalContainer("LocalContainer", self.event, {"local": self.config['utilities']['local'], "sensors": self.config['sensors'], "utilities": self.config["utilities"]["logging"]})
            threads.append(local_container)

            return threads

##################################################################
# Local Sensor                                                   #
##################################################################
    def __create_sensors(self):
            from lib.interfaces.socket.socket_writer import SocketWriter
            threads = []
            type = os.environ['TYPE']

            sensor_queue = Queue(maxsize=10)

            if type == "ash2200":
                from lib.sensors.ash2200 import ASH2200, USBSerial
                usb_serial = USBSerial(self.config['sensors']['ash2200'])
                ash2200 = ASH2200("USB", usb_serial, self.event, sensor_queue)
                threads.append(ash2200)
            elif type == "mock":
                from lib.sensors.sensor_mock import SensorMock
                mock = SensorMock("Mock", self.event, sensor_queue, self.config['sensors']['mock'])
                threads.append(mock)
            else:
                logger.error("No sensortype selected: {}".format(type))

            socket_writer = SocketWriter("SocketWriter", self.event, sensor_queue, os.environ['SOCKET'])
            threads.append(socket_writer)

            return threads

##################################################################
# Sensor Data Memcache                                                   #
##################################################################
    def __create_sensor_data_memcache(self):
            from lib.interfaces.memcache.writer.sensor_data import SensorDataWriter
            threads = []

            sensor_data_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("SensorData_Memcache_NsqReader", self.event, sensor_data_queue, self.config['interfaces']['nsq'], channel="memcache_sensor_data")
            threads.append(nsq_reader)

            sensor_data_memcache_writer = SensorDataWriter("SensorData_Memcache_Writer", self.event, sensor_data_queue, self.config['interfaces']['memcached'])
            threads.append(sensor_data_memcache_writer)

            return threads

##################################################################
# InfluxDB Writer                                                #
##################################################################
    def __create_influxdb(self):
            from lib.interfaces.influxdb.influxdb_writer import InfluxDBWriter
            threads = []

            influxdb_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("InfluxDB_NsqReader", self.event, influxdb_queue, self.config['interfaces']['nsq'], channel="influxdb")
            threads.append(nsq_reader)

            influxdb_writer = InfluxDBWriter("InfluxDB_Writer", self.event, influxdb_queue, self.config['interfaces']['influxdb'])
            threads.append(influxdb_writer)

            return threads

##################################################################
# Prometheus Writer                                              #
##################################################################
    def __create_prometheus(self):
            from lib.interfaces.prometheus.prometheus_writer import PrometheusWriter
            threads = []

            prometheus_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("Prometheus_NsqReader", self.event, prometheus_queue, self.config['interfaces']['nsq'], channel="prometheus")
            threads.append(nsq_reader)

            prometheus_writer = PrometheusWriter("Prometheus_Writer", self.event, prometheus_queue, self.config['interfaces']['prometheus'])
            threads.append(prometheus_writer)

            return threads

##################################################################
# REST                                                           #
##################################################################
    def __create_rest(self):
        from lib.interfaces.rest.rest import Rest
        threads = []

        rest = Rest("REST", self.event, self.config['interfaces']['memcached'])

        threads.append(rest)

        return threads

##################################################################
# Sensor List Memcache                                           #
##################################################################
    def __create_sensor_list_creator(self):
        from lib.utilities.sensor_list_creator import SensorListCreator
        from lib.interfaces.memcache.writer.sensor_list import SensorListWriter
        threads = []

        sensor_data_queue = Queue()

        nsq_reader = NsqReader("SensorListCreator_NsqReader", self.event, sensor_data_queue, self.config['interfaces']['nsq'], channel="memcache_sensorlist")
        threads.append(nsq_reader)

        sensor_list_queue = Queue(maxsize=10)

        sensor_list_creator = SensorListCreator("SensorListCreator", self.event, sensor_data_queue, sensor_list_queue, self.config['utilities']['sensorlist'])
        threads.append(sensor_list_creator)

        sensor_list_memcache_writer = SensorListWriter("SensorListCreator_Memcache_Writer", self.event, sensor_list_queue, self.config['interfaces']['memcached'])
        threads.append(sensor_list_memcache_writer)

        return threads
