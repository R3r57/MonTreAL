import threading
import socket
import sys
import os
from queue import Queue


class SocketReader (threading.Thread):
    def __init__(self, name, event, queue,
                 server_address="0.0.0.0", server_port=4711):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.server_address = server_address
        self.server_port = server_port
        self.queue = queue

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(0.0)  # equals non-blocking

    def run(self):
        print("Starting " + self.name)
        # Bind the socket to the port
        print('starting up on {}:{}'.format(self.server_address,
                                            str(self.server_port)))
        self.sock.bind((self.server_address, self.server_port))
        # Listen for incoming connections
        self.sock.listen(1)
        # Wait for a connection
        try:
            self.sock.makefile()
        except Exception as e:
            print("makefile", e)

        print('waiting for a connection')
        try:
            while not self.event.is_set():
                try:
                    self.sock.settimeout(None)  # equals blocking
                    connection, client_address = self.sock.accept()
                    if connection:
                        print('connection established')
                        while not self.event.is_set():
                            message = b''
                            print("Start receiving")
                            while not self.event.is_set():
                                # connection.settimeout(2)
                                # Receive the data in small chunks
                                chunk = connection.recv(1)

                                if not chunk or chunk == "\n".encode("utf-8"):
                                    # message = b''
                                    break
                                message += chunk

                            print("received via socket")
                            # : {}".format(str(message.decode("utf-8"))))
                            self.queue.put(str(message.decode("utf-8")))
                            print('no more data')

                        print("stop",
                              self.name,
                              "event is set on exit: ",
                              str(self.event.is_set()))
                except socket.timeout:
                    print("socket timeout")
                except Exception as e:
                    print("SOCKET ERROR", e)
        finally:
            # Clean up the connection
            connection.close()
