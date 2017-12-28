import json
import logging
import os

from multiprocessing import Queue
from utilities.nsq.nsq_reader import NsqReader


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class Services:
    def __init__(self, config, event):
        self.config = config
        self.event = event
        self.services = {
            "influxdb_writer": self.__create_influxdb,
            "local_manager": self.__create_local_manager,
            "prometheus_writer": self.__create_prometheus,
            "web": self.__create_web,
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
        local_configuration_path = self.config['services']['local_manager']['local_configuration']
        logger.info("Local configuration file set to {}".format(local_configuration_path))
        if os.path.isfile(local_configuration_path):
            with open(local_configuration_path, 'r') as file:
                configuration = json.load(file)
                return configuration
        else:
            logger.error("Local configuration file not found: {}".format(local_configuration_path))

    def __create_local_manager(self):
            from utilities.socket.socket_reader import SocketReader
            from utilities.local.metadata_appender import MetaDataAppender
            from utilities.local.local_manager import LocalManager
            from utilities.nsq.nsq_writer import NsqWriter

            threads = []
            local_configuration = self.__get_local_configuration()

            message_queue = Queue(maxsize=10)
            meta_queue = Queue(maxsize=10)

            socket_reader = SocketReader("SocketReader", self.event, message_queue)
            meta_data_appender = MetaDataAppender("MetaData", self.event, message_queue, meta_queue, local_configuration)
            nsq_writer = NsqWriter("NsqWriter", self.event, meta_queue, self.config['services']['nsq'])
            local_manager = LocalManager("LocalManager", self.event, {"local_manager": self.config['services']['local_manager'], "local_configuration": local_configuration, "utilities": self.config["utilities"]["logging"]})

            threads.append(socket_reader)
            threads.append(meta_data_appender)
            threads.append(nsq_writer)
            threads.append(local_manager)

            return threads

    """
    Temperature & Humidity Sensors

    """
    def __create_temperature_humidity_sensor(self):
            from utilities.socket.socket_writer import SocketWriter
            threads = []
            type = os.environ['TYPE']

            sensor_queue = Queue(maxsize=10)

            if type == "ash2200":
                from sensors.temperature_humidity.ash2200 import ASH2200, USBSerial
                usb_serial = USBSerial(self.config['configuration'])
                ash2200 = ASH2200("ASH2200", usb_serial, self.event, sensor_queue)
                threads.append(ash2200)
            elif type == "dht":
                from sensors.temperature_humidity.dht import DHT
                dht = DHT("DHT", self.config['configuration'], self.event, sensor_queue)
                threads.append(dht)
            elif type == "mock":
                from sensors.temperature_humidity.sensor_mock import SensorMock
                mock = SensorMock("Mock", self.event, sensor_queue, self.config['configuration'])
                threads.append(mock)
            elif type == "openweathermap":
                from sensors.temperature_humidity.openweathermap import OpenWeatherMap
                open_weather_map = OpenWeatherMap("OpenWeatherMap", self.config['configuration'], self.event, sensor_queue)
                threads.append(open_weather_map)
            else:
                logger.error("No sensortype selected: {}".format(type))

            socket_writer = SocketWriter("SocketWriter", self.event, sensor_queue, os.environ['SOCKET'])
            threads.append(socket_writer)

            return threads


    """
    Sensor Data Memcache Writer

    """
    def __create_sensor_data_memcache(self):
            from memcache.writer.sensor_data import SensorDataWriter
            threads = []

            sensor_data_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("SensorData_Memcache_NsqReader", self.event, sensor_data_queue, self.config['services']['nsq'], channel="memcache_sensor_data")
            sensor_data_memcache_writer = SensorDataWriter("SensorData_Memcache_Writer", self.event, sensor_data_queue, self.config['services']['memcached'])

            threads.append(nsq_reader)
            threads.append(sensor_data_memcache_writer)

            return threads


    """
    InfluxDB Writer

    """
    def __create_influxdb(self):
            from databases.influxdb.influxdb_writer import InfluxDBWriter
            threads = []

            influxdb_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("InfluxDB_NsqReader", self.event, influxdb_queue, self.config['services']['nsq'], channel="influxdb_writer")
            influxdb_writer = InfluxDBWriter("InfluxDB_Writer", self.event, influxdb_queue, self.config['services']['influxdb_writer'])

            threads.append(nsq_reader)
            threads.append(influxdb_writer)

            return threads


    """
    Prometheus Writer

    """
    def __create_prometheus(self):
            from databases.prometheus.prometheus_writer import PrometheusWriter
            threads = []

            prometheus_queue = Queue(maxsize=10)

            nsq_reader = NsqReader("Prometheus_NsqReader", self.event, prometheus_queue, self.config['services']['nsq'], channel="prometheus_writer")
            prometheus_writer = PrometheusWriter("Prometheus_Writer", self.event, prometheus_queue, self.config['services']['prometheus_writer'])

            threads.append(nsq_reader)
            threads.append(prometheus_writer)

            return threads


    """
    Web

    """
    def __create_web(self):
        from web.web import Web
        threads = []

        web = Web("Web", self.event, self.config['services']['memcached'])

        threads.append(web)

        return threads


    """
    Sensor List Memcache Writer

    """
    def __create_sensor_list_creator(self):
        from utilities.sensor_list_creator import SensorListCreator
        from memcache.writer.sensor_list import SensorListWriter
        threads = []

        sensor_data_queue = Queue()
        sensor_list_queue = Queue(maxsize=10)

        nsq_reader = NsqReader("SensorListCreator_NsqReader", self.event, sensor_data_queue, self.config['services']['nsq'], channel="memcache_sensorlist")
        sensor_list_creator = SensorListCreator("SensorListCreator", self.event, sensor_data_queue, sensor_list_queue, self.config['services']['sensorlist'])
        sensor_list_memcache_writer = SensorListWriter("SensorListCreator_Memcache_Writer", self.event, sensor_list_queue, self.config['services']['memcached'])

        threads.append(sensor_list_creator)
        threads.append(nsq_reader)
        threads.append(sensor_list_memcache_writer)

        return threads
