import logging, threading, json, os, time

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class SensorListCreator(threading.Thread):

    def __init__(self, name, event, input_queue, output_queue, config):
        super(SensorListCreator, self).__init__()
        self.name = name
        self.event = event
        self.config = config
        self.input_queue = input_queue
        self.output_queue = output_queue
        logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

    def run(self):
        logger.info("Started {}".format(self.name))
        while not self.event.is_set():
            self.event.wait(5)
            sensors = { "sensors": { "buildings": {} }, "timestamp": {}}
            data = []
            while not self.input_queue.empty():
                sensor_data = json.loads(self.input_queue.get().replace("\'", "\""))
                sensors = self.__update_sensors(sensors, sensor_data)
            sensors['timestamp'] = int(time.time())
            self.output_queue.put(str(sensors))
            logger.info("Updated sensors list and put into queue: {}".format(str(sensors)))
            self.event.wait(self.config['interval'])
        logger.info("Stopped: {}".format(self.name))

    def __update_sensors(self, sensors, data):
        building = data['building']
        room = data['room']
        machine_id = data['machine_id']
        sensor_id = data['sensor_id']

        if building not in sensors['sensors']['buildings']:
            sensors['sensors']['buildings'].update({ building: {}})
        if room not in sensors['sensors']['buildings'][building]:
            sensors['sensors']['buildings'][building].update({ room: { "devices": {}}})
        if machine_id not in sensors['sensors']['buildings'][building][room]['devices']:
            sensors['sensors']['buildings'][building][room]['devices'].update({ machine_id: { "sensors": []}})
        if sensor_id not in sensors['sensors']['buildings'][building][room]['devices'][machine_id]['sensors']:
            sensors['sensors']['buildings'][building][room]['devices'][machine_id]['sensors'].append(sensor_id)

        return sensors
