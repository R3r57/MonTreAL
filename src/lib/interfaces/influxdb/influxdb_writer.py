import logging, os, threading, json
from influxdb import client as influxdb

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class InfluxDBWriter(threading.Thread):
    def __init__(self, name, event, queue, config):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.config = config
        self.influxdb = influxdb.InfluxDBClient("influxdb", 8086, "root", "root", "montreal")
        self.influxdb.create_database("montreal")
        logger.info("{} initialized successfully".format(self.name))


    def run(self):
        logger.info("Started {}".format(self.name))
        while not self.event.is_set():
            self.event.wait(1)
            while not self.queue.empty():
                data = json.loads(self.queue.get()) # .replace("\'", "\""))
                influxdb_format = self.__convert(data)
                self.__send_data(influxdb_format.get())
                logger.info("Received data from queue and put into Influxdb")
        logger.info("Stopped {}".format(self.name))

    def __convert(self, data):
        influxdb_json = InfluxDBFormat("Temperature/Humidity")
        influxdb_json.add_tag("sensor_id", data['sensor_id'])
        influxdb_json.add_tag("hostname", data['hostname'])
        influxdb_json.add_tag("machine_id", data['machine_id'])
        influxdb_json.add_tag("building", data['building'])
        influxdb_json.add_tag("room", data['room'])
        for mes in data['measurements']:
            influxdb_json.add_measurement(mes['name'], mes['value'])
        return influxdb_json

    def __send_data(self, line):
        self.influxdb.write_points(line)


class InfluxDBFormat:
    def __init__(self, measurement):
        self.data = { "measurement": measurement, "tags": {}, "fields": {}}

    def add_tag(self, tag, value):
        self.data['tags'].update({tag: value})

    def add_measurement(self, type, value):
        self.data['fields'].update({type: value})

    def get(self):
        return [self.data]

    def __str__(self):
        return json.dumps(self.data, indent=2)
