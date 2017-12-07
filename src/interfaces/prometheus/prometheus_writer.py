import json
import logging
import os
import threading

from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY, GaugeMetricFamily


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class PrometheusWriter(threading.Thread):
    def __init__(self, name, event, queue, config):
        super(PrometheusWriter, self).__init__()
        self.name = name
        self.event = event
        self.queue = queue
        self.config = config

        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started {}".format(self.name))
        collectors = {}
        start_http_server(self.config['port'])
        while not self.event.is_set():
            self.event.wait(2)
            while not self.queue.empty():
                data = json.loads(self.queue.get())
                key = "{}:{}:{}:{}".format(data['hostname'], data['device_id'], data['type'], data['sensor_id'])
                if key in collectors:
                    REGISTRY.unregister(collectors[key])
                    collectors.pop(key, None)
                collector = SensorDataCollector(key, data)
                REGISTRY.register(collector)
                collectors.update({ key: collector })
                logger.info("Received data from queue and prepared for Prometheus")
        logger.info("Stopped {}".format(self.name))


class SensorDataCollector(object):
    def __init__(self, key, data):
        self.key = key
        self.hostname = data['hostname']
        self.device_id = data['device_id']
        self.building = data['building']
        self.room = data['room']
        self.sensor_id = data['sensor_id']
        self.type = data['type']
        self.measurements = data['measurements']

    def collect(self):
        gc = GaugeMetricFamily('montreal:{}'.format(self.key.replace("-", "_")), "documentation_placeholder", labels=['hostname', 'device_id', 'building', 'room', 'sensor_id', 'type', 'name'])
        for mes in self.measurements:
            gc.add_metric([self.hostname, self.device_id, self.building, self.room, str(self.sensor_id), str(self.type), mes['name']], mes['value'])
        yield gc
