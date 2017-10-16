#!/usr/bin/env python3

from lib.prtg.prtg_api import prtg_api
from multiprocessing import Queue
import threading
import json
import os


class prtg_thread(threading.Thread):

    def __init__(self, event, queue, config=None):
        self.queue = queue
        self.event = event
        self.keys = ["hostname", "machine_id", "room", "library", "sensor_id"]
        threading.Thread.__init__(self)
        if config is None:
            config = {}
        if not self.__keylist_in_dict(["timeout_nsq", "timeout_prtg"], config):
            config.update({'timeout_nsq': "5", 'timeout_prtg': "30"})
        self.config = config
        if not self.__keylist_in_dict(["username", "passhash"], config):
            config.update(json.loads(self.get_secret("PRTG_CREDENTIALS")))

        self.api = prtg_api(config['username'], config['passhash'])

    def get_secret(self, secretname):
        secretfile = "/run/secrets/" + secretname
        if os.path.isfile(secretfile):
            with open(secretfile, "r") as secret_file:
                data = secret_file.read()
            return data
        return None

    def run(self):
        self.event.wait(10)
        self.__refresh_prtg_sensors()
        self.__read_queue()
        count = 0
        while not self.event.is_set():
            self.event.wait(timeout=60 * int(self.config['timeout_nsq']))
            if not self.event.is_set():
                if count == int(int(self.config['timeout_prtg']) / int(self.config['timeout_nsq'])):
                    self.__refresh_prtg_sensors()
                    count = 0
                else:
                    count += 1
                self.__read_queue()
        print("Stopping PRTG_Thread")

    def __refresh_prtg_sensors(self):
        print("Refresh PRTG Sensors")
        self.api.get_prtg_sensors()

    def __read_queue(self):
        while not self.queue.empty():
            data = json.loads(self.queue.get().replace("'", "\""))
            print("Read Queue Data")
            if self.__keylist_in_dict(self.keys, data):
                url = "/prtg/{}_{}/{}".format(str(data['hostname']),
                                              str(data['machine_id']),
                                              str(data['sensor_id']))
                desc = "{}~{}~{}".format(str(data['hostname']),
                                         str(data['sensor_id']),
                                         str(data['machine_id']))
                self.api.add_sensor(description=desc,
                                    url=url,
                                    room=data['room'],
                                    location=data['library'],
                                    sensor_id=str(data['sensor_id']))

    def __keylist_in_dict(self, keylist, dicti):
        for key in keylist:
            if key not in dicti:
                return False
        return True
