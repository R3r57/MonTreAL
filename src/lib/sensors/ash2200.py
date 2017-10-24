import logging, serial, json, threading, os
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
                print("connected to {}: waiting...".format(self.port))
                data = usb.readline().decode().strip()
                if data:
                    print("data received: {}".format(data))
                    return data
                print("nothing received")
        except serial.SerialException as e:
            raise


class ASH2200(threading.Thread):

    def __init__(self, name, usb_serial, event, queue):
        threading.Thread.__init__(self)
        self.name = name
        self.usb_serial = usb_serial
        self.queue = queue
        self.event = event
        print("initialized")

    def run(self):
        print("starting...")
        while not self.event.is_set():
            try:
                logger.info("Waiting for data from usb...")
                data = self.usb_serial.read()
                if data:
                    converted_data = self.convert(data)
                    for item in converted_data:
                        self.queue.put(json.dumps(item))
                        print("message {}", item)
                        print("data put into queue")
            except Exception:
                raise
        print("Stopped")

    def convert(self, string):
        data = []
        splitted = string.split(';')
        for id in range(1, 9):
            temp = splitted[(id + 2)].replace(",", ".")
            hum = splitted[(id + 10)].replace(",", ".")
            if temp and hum:
                data.append(Measurement(id, temp, hum).to_json())
        print("data converted: {}".format([e for e in data]))
        return data
