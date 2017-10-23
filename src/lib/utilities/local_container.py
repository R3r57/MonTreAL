import socket, docker, threading, json, os, base64, logging

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class LocalContainer (threading.Thread):
    def __init__(self, name, event, config):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.config = config
        self.container = None
        self.dcli = docker.DockerClient.from_env()
        logger.info("{} initialized successfully".format(self.name))

    def __clean_old(self):
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

    def __get_ip_address(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("nsqd", 4151))
            myip = s.getsockname()[0]
        return myip

    def __b64_enc(self, data):
        return base64.encodebytes(json.dumps(data).encode())

    def __b64_dec(self, data):
        return json.loads(base64.decodebytes(data).decode())

    def __create_container(self):
        logger.info("Creating container...")
        image = self.config["local"]["image"]
        label = self.config["local"]['label']
        environment = self.config["local"]["environment"]
        environment.update({"CONFIG": "{}".format(self.__b64_enc(self.config["sensors"]))})
        environment.update({"SOCKET": "{}".format(self.__get_ip_address(), 4711)})

        try:
            device = [self.config["local"]["device"] + ":" + self.config["local"]["device"]]
        except KeyError:
            device = []
        try:
            command = self.config["local"]["command"]
        except KeyError:
            command = None

        self.container = self.dcli.containers.create(image,
                                                     command=command,
                                                     tty=True,
                                                     devices=device,
                                                     environment=environment,
                                                     labels={label: ""},
                                                     network=self.config["local"]["network_name"],
                                                     volumes=[])
        logger.info("...success")

    def run(self):
        logger.info("Started: {}".format(self.name))
        while not self.event.is_set():
            self.__clean_old()
            if len(self.dcli.containers.list(filters={"label": self.config["local"]['label']})) == 0:
                self.__create_container()
                self.container.start()
                self.event.wait(30)
            if self.container.status in ["running", "created"]:
                self.event.wait(30)
            else:
                logger.info(json.dumps(self.container.attrs, indent=4))
                self.__clean_old()
                self.container = None
        if self.container:
            self.container.remove(force=True, v=True)
            self.container = None
