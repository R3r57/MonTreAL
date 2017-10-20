import socket
import docker
import threading
import json
import os
import base64
import logging

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class LocalContainer (threading.Thread):
    def __init__(self, name, event, config):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.config = config
        self.dcli = docker.DockerClient.from_env()
        self.container = None
        logger.info("{} initialized successfully".format(self.name))

    def run(self):
        logger.info("Started: {}".format(self.name))
        # self.pull_image()
        while not self.event.is_set():
            self.clean_old()
            if len(self.dcli.containers.list(filters={"label": self.config["local"]['label']})) == 0:
                self.create_container()
                self.container.start()
                self.event.wait(30)
            if self.container.status in ["running", "created"]:
                self.event.wait(30)
            else:
                print(json.dumps(self.container.attrs, indent=4))
                self.clean_old()
                self.container = None
        if self.container:
            self.container.remove(force=True, v=True)
            self.container = None

    def clean_old(self):
        logger.info("Cleaning old container...")
        containerlist = self.dcli.containers.list(filters={"label": self.config["local"]['label']}, all=True)
        if len(containerlist) > 0:
            for container in containerlist:
                if self.container is None:
                    container.remove(force=True, v=True)
                elif self.container.id != container.id or self.container.status not in ["running", "created"]:
                    print("Cleanup container with label: ", self.config["local"]['label'])
                    print("cleanup {}: {}".format(self.container.id, self.container.status))
                    container.remove(force=True, v=True)
        logger.info("...success")

    def get_ip_address(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("nsqd", 4151))
            myip = s.getsockname()[0]
        return myip

    def b64_enc(self, data):
        return base64.encodebytes(json.dumps(data).encode())

    def b64_dec(self, data):
        return json.loads(base64.decodebytes(data).decode())

    def get_secret(self, secretname):
        secretfile = "/run/secrets/" + secretname
        if os.path.isfile(secretfile):
            with open(secretfile, "r") as secret_file:
                data = secret_file.read()
            return data
        return None

    def pull_image(self):
        username = self.get_secret("REGISTRY_USERNAME")
        password = self.get_secret("REGISTRY_PASSWORD")
        image = config["local"]['image']
        self.dcli.images.pull(image, auth_config={"username": username,
                                                  "password": password})

    def create_container(self):
        logger.info("Creating container...")
        try:
            DEVICE = [self.config["local"]["device"] + ":" + self.config["local"]["device"]]
        except KeyError:
            DEVICE = []

        ENVIRONMENT = self.config["local"]["environment"]
        ENVIRONMENT.update({"CONFIG": "{}".format(self.b64_enc(self.config["sensors"]))})
        ENVIRONMENT.update({"SOCKET": "{}".format(self.get_ip_address(), 4711)})
        try:
            COMMAND = self.config["local"]["command"]
        except KeyError:
            COMMAND = None
        LABEL = self.config["local"]['label']
        IMAGE = self.config["local"]["image"]

        self.container = self.dcli.containers.create(IMAGE,
                                                     command=COMMAND,
                                                     tty=True,
                                                     devices=DEVICE,
                                                     environment=ENVIRONMENT,
                                                     labels={LABEL: ""},
                                                     network=self.config["local"]["network_name"],
                                                     volumes=[])
        logger.info("...success")
