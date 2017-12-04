import logging
import os
import socket
import sys
import threading

from queue import Queue


logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class SocketWriter (threading.Thread):
    def __init__(self, name, event, queue, server_address="127.0.0.1", server_port=4711):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.server_address = server_address
        self.server_port = server_port
        logger.info("{} initialized successfully".format(self.name))

    def __send(self, sock, message):
        try:
            msg = str(message + "\n").encode("utf-8")
            sock.sendall(msg)
        except socket.error as msg:
            logger.error(str(msg))

    def run(self):
        logger.info("Started: {}".format(self.name))
        while not self.event.is_set():
            if not self.queue.empty():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect((self.server_address, self.server_port))
                    data = self.queue.get()
                    self.__send(sock, data)
                    logger.info("Wrote data to socket")
                except Exception as e:
                    logger.error(e)
                    self.event.wait(1);
                finally:
                    sock.close()
            else:
                self.event.wait(5)
        logger.info("Stopped: {}".format(self.name))
