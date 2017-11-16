import json
import logging
import os

from multiprocessing import Queue
from lib.interfaces.nsq.nsq_reader import NsqReader


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class Services:
    def __init__(self, config, event):
        self.config = config
        self.event = event
        self.services = {
            "influxdb_writer": self.__create_influxdb,
            "local_manager": self.__create_local_manager,
            "prometheus_writer": self.__create_prometheus,
            "rest": self.__create_rest,
            "sensor_data_memcache_writer": self.__create_sensor_data_memcache,
            "sensor_list_memcache_writer": self.__create_sensor_list_creator,
            "temperature_humidity_sensor": self.__create_temperature_humidity_sensor
        }

    def get_services(self, type):
        return self.services.get(type)()

    """
    Local Manager

    """
    def __get_local_configuration(self):
        local_configuration_path = self.config['utilities']['local_manager']['local_configuration']
        logger.info("Local configuration file set to {}".format(local_configuration_path))
        if os.path.isfile(local_configuration_path):
            with open(local_configuration_path, 'r') as file:
                configuration = json.load(file)
                return configuration
        else:
            logger.error("Local configuration file not found: {}".format(local_configuration_path))

    def __create_local_manager(self):
            from lib.interfaces.socket.socket_reader import SocketReader
            from lib.utilities.metadata_appender import MetaDataAppender
            from lib.utilities.local_manager import LocalManager
            from lib.interfaces.nsq.nsq_writer import NsqWriter
            
            threads = []
            local_configuration = self.__get_local_configuration()

            message_queue = Queue(maxsize=10)
            meta_queue = Queue(maxsize=10)

            socket_reader = SocketReader("SocketReader", self.event, message_queue)
            meta_data_appender = MetaDataAppender("MetaData", self.event, message_queue, meta_queue, local_configuration)
            nsq_writer = NsqWriter("NsqWriter", self.event, meta_queue, self.config['interfaces']['nsq'])
            local_manager = LocalManager("LocalManager", self.event, {"local_manager": self.config['utilities']['local_manager'], "local_configuration": local_configuration, "utilities": self.config["utilities"]["logging"]})

            threads.append(socket_reader)
            threads.append(meta_data_appender)
            threads.append(nsq_writer)
            threads.append(local_manager)

            return threads

    """
    Temperature & Humidity Sensors

    """
    def __create_temperature_humidity_sensor(self):
            from lib.interfaces.socket.socket_writer import SocketWriter
            threads = []
            type = os.environ['TYPE']

            sensor_queue = Queue(maxsize=10)

            if type == "ash2200":
                from lib.sensors.temperature_humidity.ash2200 import ASH2200, USBSerial
                usb_serial = USBSerial(self.config['configuration'])
                ash2200 = ASH2200("USB", usb_serial, self.event, sensor_queue)
                threads.append(ash2200)
            elif type == "mock":
                from lib.sensors.temperature_humidity.sensor_mock import SensorMock
                mock = SensorMock("Mock", self.event, sensor_queue, self.config['configuration'])
                threads.append(mock)
            else:
                logger.error("No sensortype selected: {}".format(type))

            socket_writer = SocketWriter("SocketWriter", self.event, sensor_queue, os.environ['SOCKET'])
            threads.append(socket_writer)

            return threads


    """
    Sensor Data Memcache Writer

    """
    def __create_sensor_data_memcache(self):
            from lib.interfaces.memcache.writer.sensor_data import SensorDataWriter
            threads = []

            sensor_data_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("SensorData_Memcache_NsqReader", self.event, sensor_data_queue, self.config['interfaces']['nsq'], channel="memcache_sensor_data")
            sensor_data_memcache_writer = SensorDataWriter("SensorData_Memcache_Writer", self.event, sensor_data_queue, self.config['interfaces']['memcached'])

            threads.append(nsq_reader)
            threads.append(sensor_data_memcache_writer)

            return threads


    """
    InfluxDB Writer

    """
    def __create_influxdb(self):
            from lib.interfaces.influxdb.influxdb_writer import InfluxDBWriter
            threads = []

            influxdb_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("InfluxDB_NsqReader", self.event, influxdb_queue, self.config['interfaces']['nsq'], channel="influxdb")
            influxdb_writer = InfluxDBWriter("InfluxDB_Writer", self.event, influxdb_queue, self.config['interfaces']['influxdb'])

            threads.append(nsq_reader)
            threads.append(influxdb_writer)

            return threads


    """
    Prometheus Writer

    """
    def __create_prometheus(self):
            from lib.interfaces.prometheus.prometheus_writer import PrometheusWriter
            threads = []

            prometheus_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("Prometheus_NsqReader", self.event, prometheus_queue, self.config['interfaces']['nsq'], channel="prometheus")
            prometheus_writer = PrometheusWriter("Prometheus_Writer", self.event, prometheus_queue, self.config['interfaces']['prometheus'])

            threads.append(nsq_reader)
            threads.append(prometheus_writer)

            return threads


    """
    REST

    """
    def __create_rest(self):
        from lib.interfaces.rest.rest import Rest
        threads = []

        rest = Rest("REST", self.event, self.config['interfaces']['memcached'])

        threads.append(rest)

        return threads


    """
    Sensor List Memcache Writer

    """
    def __create_sensor_list_creator(self):
        from lib.utilities.sensor_list_creator import SensorListCreator
        from lib.interfaces.memcache.writer.sensor_list import SensorListWriter
        threads = []

        sensor_data_queue = Queue()
        sensor_list_queue = Queue(maxsize=10)

        nsq_reader = NsqReader("SensorListCreator_NsqReader", self.event, sensor_data_queue, self.config['interfaces']['nsq'], channel="memcache_sensorlist")
        sensor_list_creator = SensorListCreator("SensorListCreator", self.event, sensor_data_queue, sensor_list_queue, self.config['utilities']['sensorlist'])
        sensor_list_memcache_writer = SensorListWriter("SensorListCreator_Memcache_Writer", self.event, sensor_list_queue, self.config['interfaces']['memcached'])

        threads.append(sensor_list_creator)
        threads.append(nsq_reader)
        threads.append(sensor_list_memcache_writer)

        return threads
