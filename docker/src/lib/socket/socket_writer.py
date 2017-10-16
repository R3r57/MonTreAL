import threading
import socket
import sys
import os
from queue import Queue


class SocketWriter (threading.Thread):
    def __init__(self, name, event, queue,
                 server_address="127.0.0.1", server_port=4711):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.queue = queue
        self.server_address = server_address
        self.server_port = server_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        print("Starting " + self.name)
        try:
            self.sock.connect((self.server_address, self.server_port))

            while not self.event.is_set():
                self.event.wait(5)
                while not self.queue.empty():
                    print("write on sock")
                    data = self.queue.get()
                    print(data)
                    self.send(data)
                    self.queue.task_done()
        finally:
            print(sys.stderr, 'closing socket')
            self.sock.close()

    def send(self, message):
        try:
            # Send data
            # print(sys.stderr, 'sending "%s"' % message)
            msg = str(message + "\n").encode("utf-8")  # str.encode(message)
            self.sock.sendall(msg)
        except socket.error as msg:
            print(sys.stderr, msg)
            # sys.exit(1)
