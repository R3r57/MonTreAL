import json
import logging
import os
import threading
import serial

from lib.sensors.data import Measurement


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class USBSerial:

    def __init__(self, config):
        self.port = config['device']
        self.baudrate = config['baudrate']
        self.timeout = config['timeout']

    def read(self):
        try:
            with serial.Serial(port=self.port,
                               baudrate=self.baudrate,
                               timeout=self.timeout) as usb:
                logger.info("Connected to {}: waiting...".format(self.port))
                data = usb.readline().decode().strip()
                if data:
                    logger.info("Data received: {}".format(data))
                    return data
        except serial.SerialException as e:
            raise


class ASH2200(threading.Thread):

    def __init__(self, name, usb_serial, event, queue):
        threading.Thread.__init__(self)
        self.type = "ASH2200"
        self.name = name
        self.usb_serial = usb_serial
        self.queue = queue
        self.event = event
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started: {}".format(self.name))
        while not self.event.is_set():
            try:
                logger.info("Waiting for data from usb...")
                data = self.usb_serial.read()
                if data:
                    converted_data = self.convert(data)
                    for item in converted_data:
                        self.queue.put(json.dumps(item))
                        logger.info("Data put into queue")
            except Exception:
                raise
        logger.info("Stopped: {}".format(self.name))

    def convert(self, string):
        data = []
        splitted = string.split(';')
        for id in range(1, 9):
            temp = splitted[(id + 2)].replace(",", ".")
            hum = splitted[(id + 10)].replace(",", ".")
            if temp and hum:
                data.append(Measurement(id, self.type, temp, hum).to_json())
        logger.info("data converted: {}".format([e for e in data]))
        return data
