import logging, threading, socket, sys, os
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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info("{} initialized successfully".format(self.name))

    def __send(self, message):
        try:
            msg = str(message + "\n").encode("utf-8")
            self.sock.sendall(msg)
        except socket.error as msg:
            logger.error(str(msg))

    def run(self):
        logger.info("Started: {}".format(self.name))
        try:
            self.sock.connect((self.server_address, self.server_port))
            while not self.event.is_set():
                self.event.wait(5)
                while not self.queue.empty():
                    data = self.queue.get()
                    self.__send(data)
                    self.queue.task_done()
                    logger.info("Wrote data to socket")
        finally:
            logger.info("Stopped: {}".format(self.name))
            self.sock.close()
