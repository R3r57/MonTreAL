import logging, os, threading, json
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

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
                key = "{}_{}_{}".format(data['hostname'], data['machine_id'], data['sensor_id'])
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
        self.machine_id = data['machine_id']
        self.building = data['building']
        self.room = data['room']
        self.sensor_id = data['sensor_id']
        self.measurements = data['measurements']

    def collect(self):
        gc = GaugeMetricFamily('SensorData_{}'.format(self.key), "documentation_placeholder", labels=['hostname', 'machine_id', 'building', 'room', 'sensor_id', 'type'])
        for mes in self.measurements:
            gc.add_metric([self.hostname, self.machine_id, self.building, self.room, str(self.sensor_id), mes['name']], mes['value'])
        yield gc
