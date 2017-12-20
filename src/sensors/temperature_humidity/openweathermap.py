import logging
import os
import urllib3
import json

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

from sensors.meta.data import Measurement
from sensors.meta.sensor import AbstractSensor

class OpenWatherMap(AbstractSensor):

    def __init__(self, name, config, event, queue):
        super(OpenWatherMap, self).__init__(name,config, event, queue)
        self.id = config['id']
        self.key = config['key']
        self.city = config['city']
        self.country = config['country']
        self.interval = config['interval']
        self.url = "https://api.openweathermap.org/data/2.5/weather?appid={}&q={},{}".format(self.key, self.city, self.country)
        self.type = "OpenWeatherMap_{}".format(self.city)
        self.connection_pool = urllib3.PoolManager()
        logger.info("{} initialized successfully".format(self.name))

    def read(self):
        self.event.wait(self.interval)
        logger.info("Fetching data from OpenWatherMap...")
        request = self.connection_pool.request('GET', self.url)
        data = json.loads(request.data.decode('utf-8'))
        if data:
            temp = data['main']['temp'] - 273.15
            hum = data['main']['humidity']
            measurement = Measurement(self.id, self.type, temp, hum).to_json()
            logger.info("Data received: {}".format(measurement))
        return [measurement]