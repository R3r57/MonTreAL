#!/usr/bin/env python3
import datetime
import json
import logging
import os
import signal
import sys
import threading
import time

from utilities.configuration import ConfigurationReader
from utilities.logging.logger import LoggerFactory
from services import Services


configuration = ConfigurationReader.get()
logger = LoggerFactory(configuration['utilities']['logging']).create_logger()
logger = logging.LoggerAdapter(logger, {"class": os.path.basename(__file__)})

class Manager:

    def __init__(self, service_type):
        self.threads = []
        self.service_type = service_type
        self.config = configuration
        self.event = threading.Event()
        self.__register_signals()
        logger.info("Main program for {} initialized successfully".format(service_type))

    def __register_signals(self):
        signal.signal(signal.SIGHUP, self.__handle_signals)
        signal.signal(signal.SIGINT, self.__handle_signals)
        signal.signal(signal.SIGTERM, self.__handle_signals)

    def __handle_signals(self, signum, stack):
        logger.info("Signal {} caught".format(signum))
        self.__terminate_threads()

    def __create_threads(self):
        logger.info("Creating threads for {}...".format(self.service_type))
        threads = Services(self.config, self.event).get_services(self.service_type)
        self.__register_threads(threads)

    def __register_threads(self, threads):
        for t in threads:
            if t not in self.threads:
                self.threads.append(t)
                logger.info("Add thread {} as {}".format(t.name, len(self.threads)))

    def __start_threads(self):
        logging.info("Starting threads...")
        for t in self.threads:
            t.start()
            logging.info("{} started".format(t.name))

    def __terminate_threads(self):
        logger.info("Terminating...")
        self.event.set()
        start = datetime.datetime.now()
        counter = 1
        while not len(self.threads) == 0:
            for t in self.threads:
                if not t.isAlive():
                    self.threads.remove(t)
                else:
                    t.join(timeout=5)
                    logger.info("Joining {} (attempt: {})".format(t.name, counter))
            counter += 1
            if counter >= 10:
                logger.error("Unable to join all threads after {} attempts...exiting!".format(str(counter)))
                break
        logger.info("Duration till exit: {}".format(str(datetime.datetime.now() - start)))
        sys.exit(0)

    def __restart(self):
            logger.info("Restarting {}...".format(self.service_type))
            self.__terminate_threads()
            self.event.clear()
            self.threads = []
            self.__create_threads()
            self.__start_threads()

    def run(self):
        self.__create_threads()
        self.__start_threads()
        while not self.event.is_set():
            self.event.wait(30)
            for t in self.threads:
                if not t.isAlive():
                    logger.error("Thread died: {}".format(t))
                    self.__restart()
                    break

if __name__ == '__main__':
    service_type = None
    if "SERVICE" in os.environ:
        service_type = os.environ['SERVICE']
        logger.info("Starting service {}".format(service_type))
        p = Manager(service_type)
        p.run()
        logger.info("Manager for {} is running".format(service_type))
