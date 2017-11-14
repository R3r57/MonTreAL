import socket, docker, threading, json, os, base64, logging

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class LocalManager (threading.Thread):
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
        containerlist = self.dcli.containers.list(filters={"label": self.config["local_manager"]['label']}, all=True)
        if len(containerlist) > 0:
            for container in containerlist:
                if self.container is None:
                    container.remove(force=True, v=True)
                elif self.container.id != container.id or self.container.status not in ["running", "created"]:
                    logger.info("Cleanup container with label: ", self.config["local_manager"]['label'])
                    logger.info("cleanup {}: {}".format(self.container.id, self.container.status))
                    container.remove(force=True, v=True)

    def __get_ip_address(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("nsqd", 4151))
            myip = s.getsockname()[0]
        return myip

    def __create_container(self):
        logger.info("Creating container...")
        label = self.config['local_manager']['label']
        image = "{}-{}".format(self.config['local_manager']['image'], self.config['local_configuration']['meta']['architecture'])

        devices = []
        command = None
        sensors = self.config['local_configuration']['sensor']
        if sensors['service'] and sensors['type']:
            environment = { "SERVICE": sensors['service'], "TYPE": sensors['type'] }
            for device in sensors['devices']:
                devices.append("{}:{}".format(device, device))
            if sensors['command']:
                command = sensors['command']
        else:
            environment = self.config["local_manager"]["global_sensor_configuration"]
            for device in self.config['local_manager']['devices']:
                devices.append("{}:{}".format(device, device))
            if self.config['local_manager']['command']:
                command = self.config["local_manager"]["command"]

        environment.update({"CONFIG": "{{ 'sensors': {}, 'utilities': {{ 'logging': {}}}}}".format(self.config["sensors"], self.config["utilities"])})
        environment.update({"SOCKET": "{}".format(self.__get_ip_address())})

        self.container = self.dcli.containers.create(image,
                                                     command=command,
                                                     name = "sensor_container",
                                                     tty=True,
                                                     devices=devices,
                                                     environment=environment,
                                                     labels={label: ""},
                                                     network=self.config["local_manager"]["network_name"],
                                                     volumes=[])
        logger.info("...success")

    def run(self):
        logger.info("Started: {}".format(self.name))
        while not self.event.is_set():
            self.__clean_old()
            if len(self.dcli.containers.list(filters={"label": self.config["local_manager"]['label']})) == 0:
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
