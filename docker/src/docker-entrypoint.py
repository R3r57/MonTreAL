#!/usr/bin/env python3

import docker
import os
import signal
import threading
import time
import json
import sys
import datetime

from multiprocessing import Queue as mpQueue
from queue import Queue

from lib.local_container import LocalContainer

from lib.socket.socket_reader import SocketReader
from lib.socket.socket_writer import SocketWriter

from lib.nsq.nsq_reader import NsqReader
from lib.nsq.nsq_writer import NsqWriter

from lib.prtg.web import PRTGweb
from lib.prtg.memcached import Memcached
from lib.prtg.converter import PRTGconverter
from lib.prtg.sensor_overwatch import prtg_thread
from lib.prtg.sensor_list import SensorList

from lib.prtg.prtg import PRTG
from lib.prtg.raw import RawMem

from lib.sensor.usb_mock import USBmock
from lib.sensor.ash2200 import ASH2200, USBSerial
from lib.sensor.metadata_appender import MetaDataAppender


class MainProgramm:

    def __init__(self, service_type):
        self.service_type = service_type
        self.config = self.__get_config()
        self.event = threading.Event()
        self.threads = []
        self.register_signals()

    def register_signals(self):
        signal.signal(signal.SIGHUP, self.handle_signals)
        signal.signal(signal.SIGINT, self.handle_signals)
        signal.signal(signal.SIGTERM, self.handle_signals)
        # signal.signal(signal.SIGKILL, self.handle_signals)

    def __get_config(self):
        if "CONFIG_FILE" in os.environ:
            secretfile = os.environ['CONFIG_FILE']
        else:
            secretfile = os.getcwd() + "/config.json"
        print("CONFIG_FILE: ", secretfile)
        if os.path.isfile(secretfile):
            with open(secretfile, "r") as secret_file:
                data = json.load(secret_file)
            return data
        return None

    def handle_signals(self, signum, stack):
        print("Signal {} caught".format(signum))
        self.start = datetime.datetime.now()
        self.terminate_threads()

    def __terminate_threads(self):
        self.event.set()
        time.sleep(0.2)
        while not len(self.threads) == 0:
            for t in self.threads:
                t.join(timeout=0.2)
                print("joining ", t.name)
                if not t.isAlive():
                    self.threads.remove(t)
                    break

    def terminate_threads(self):
        self.__terminate_threads()
        print("Duration till exit: ", str(datetime.datetime.now() - self.start))
        sys.exit(0)

    def __register_thread(self, t):
        print("add thread {} as {}".format(t.name, len(self.threads)))
        if t not in self.threads:
            self.threads.append(t)

    def __start_threads(self):
        for t in self.threads:
            t.start()

    def __create_threads(self):

        if self.service_type == "manager":
            self.__create_manager()
            self.__create_docker()

        elif self.service_type == "prtgconvert":
            self.__create_prtgconvert()

        elif self.service_type == "prtgweb":
            self.__create_prtgweb()

        elif self.service_type == "prtgregister":
            self.__create_prtgregister()

        elif self.service_type == "sensor":
            self.__create_sensor()

        elif self.service_type == "rawjson":
            self.__create_rawjson()

        elif self.service_type == "sensorlist":
            self.__create_sensorlist()

        else:
            print("No service selected. Please set 'SERVICE' as environment variable with:")
            print("manager|prtgconvert|prtgweb|sensor|all")

        self.__start_threads()

    def run(self):
        self.__create_threads()
        print("main loop event is set: ", str(self.event.is_set()))
        while not self.event.is_set():
            restart = False
            self.event.wait(30)
            for t in self.threads:
                if not t.isAlive():
                    restart = True
                    break
            if restart:
                self.__terminate_threads()
                self.event.clear()
                self.threads = []
                self.__create_threads()
        print("main loop event is set on exit: ", str(self.event.is_set()))

    def __create_manager(self):
            message_queue = Queue(maxsize=10)
            socket = SocketReader("SocketReader",
                                  self.event,
                                  message_queue)
            self.__register_thread(socket)

            meta_queue = Queue(maxsize=10)
            nsqW = NsqWriter("NsqWriter",
                             self.event,
                             meta_queue,
                             self.config["nsq"])
            self.__register_thread(nsqW)

            meta = MetaDataAppender("MetaData",
                                    self.event,
                                    message_queue,
                                    meta_queue,
                                    self.config['metadata'])
            self.__register_thread(meta)


    def __create_docker(self):
            container = LocalContainer("LocalContainer",
                                       self.event,
                                       {"local": self.config['local'],
                                        "sensors": self.config['sensors']})
            self.__register_thread(container)


    def __create_prtgconvert(self):
            update_queue = mpQueue(maxsize=10)
            nsqR = NsqReader("NsqReader",
                             self.event,
                             update_queue,
                             self.config["nsq"],
                             channel="PRTGconverter")
            self.__register_thread(nsqR)

            prtgconv = PRTGconverter("PRTGconverter",
                                     self.event,
                                     update_queue,
                                     self.config["memcached"])
            self.__register_thread(prtgconv)


    def __create_prtgweb(self):
            prtgweb = PRTGweb("PRTGweb", self.event, self.config["memcached"])
            self.__register_thread(prtgweb)

    def __create_prtgregister(self):
            message_queue = mpQueue()
            nsq_r = NsqReader("nsq_reader",
                              self.event,
                              message_queue,
                              self.config["nsq"],
                              channel="sensor_overwatcher")
            self.__register_thread(nsq_r)

            # Compare with existing PRTG sensors
            sensor_overwatcher = prtg_thread(self.event, message_queue)
            self.__register_thread(sensor_overwatcher)


    def __create_sensor(self):
            usb_queue = Queue()
            socket = SocketWriter("SocketWriter",
                                  self.event,
                                  usb_queue,
                                  os.environ['SOCKET'])
            self.__register_thread(socket)

            usb_serial = USBSerial("/dev/ttyUSB0", 9600, 20)
            ash2200 = ASH2200("USB", usb_serial, self.event, usb_queue)
            self.__register_thread(ash2200)


    def __create_rawjson(self):
            update_queue = mpQueue(maxsize=10)
            nsqR = NsqReader("NsqReader",
                             self.event,
                             update_queue,
                             self.config["nsq"],
                             channel="RawMem")
            self.__register_thread(nsqR)

            rawmem = RawMem("RAWMem", self.event, update_queue, self.config["memcached"])
            self.__register_thread(rawmem)

    def __create_sensorlist(self):
            update_queue = mpQueue()
            nsqR = NsqReader("NsqReader",
                             self.event,
                             update_queue,
                             self.config["nsq"],
                             channel="SensorList")
            self.__register_thread(nsqR)

            slist = SensorList("SensorList", self.event, update_queue)
            self.__register_thread(slist)


if __name__ == '__main__':

    print("#" * 10)
    print("Montreal")
    print("#" * 10)

    service_type = None
    if "SERVICE" in os.environ:
        service_type = os.environ['SERVICE']
        print("Start Service: ", service_type)
        p = MainProgramm(service_type)
        p.run()
        print("main running")
