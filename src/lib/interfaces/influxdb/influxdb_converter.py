import logging, os, json

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class InfluxDBConverter:

    def __init__(self, name):
        self.name = name

    def convert(self, data):
        influxdb_json = InfluxDBFormat(self.name)
        influxdb_json.add_tag("sensor_id", data['sensor_id'])
        influxdb_json.add_tag("hostname", data['hostname'])
        influxdb_json.add_tag("device_id", data['device_id'])
        influxdb_json.add_tag("building", data['building'])
        influxdb_json.add_tag("room", data['room'])
        for mes in data['measurements']:
            influxdb_json.add_measurement(mes['name'], mes['value'])
        return influxdb_json

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
