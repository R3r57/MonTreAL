import socket, docker, threading, json, os, base64, logging

logger = logging.LoggerAdapter(logging.getLogger("montreal"), {"class": os.path.basename(__file__)})

class LocalManager (threading.Thread):
    def __init__(self, name, event, config):
        threading.Thread.__init__(self)
        self.name = name
        self.event = event
        self.config = config
        self.containers = []
        self.dcli = docker.DockerClient.from_env()
        logger.info("{} initialized successfully".format(self.name))

    def __clean_old(self):
        logger.info("Cleaning old container...")
        containerlist = self.dcli.containers.list(filters={"label": self.config["local_manager"]['label']}, all=True)
        if len(containerlist) > 0:
            for container in containerlist:
                container.remove(force=True, v=True)
                logger.info("Removed old container: {} {} {}".format(container.name, container.id, container.status))

    def __get_ip_address(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("nsqd", 4151))
            myip = s.getsockname()[0]
        return myip

    def __initialize_containers(self):
        self.__clean_old()
        logger.info("Creating containers...")
        containers = []
        label = self.config['local_manager']['label']
        image = "{}-{}".format(self.config['local_manager']['image'], self.config['local_configuration']['meta']['architecture'])
        if len(self.config['local_configuration']['sensors']) > 0:
            for sensor, configuration  in self.config['local_configuration']['sensors'].items():
                containers.append(self.__create_container(image, label, sensor, configuration))
        else:
            for sensor, configuration in self.config['local_manager']['global_sensors'].items():
                containers.append(self.__create_container(image, label, sensor, configuration))
        return containers

    def __create_container(self, image, label, sensor, configuration):
        devices = []
        command = None
        environment = {"CONFIG": "{{ 'sensors': {}, 'utilities': {{ 'logging': {}}}}}".format(self.config["sensors"],self.config["utilities"])}
        environment.update({ "SOCKET": "{}".format(self.__get_ip_address())})
        environment.update({ "SERVICE": configuration['service'], "TYPE": configuration['type']})
        for device in configuration['devices']:
            devices.append("{}:{}".format(device, device))
        if configuration['command']:
            command = configuration['command']
        container = self.dcli.containers.create(image, command=command, name = "{}_{}".format(sensor, configuration['type']), tty=True, devices=devices, environment=environment, labels={label: ""}, network=self.config["local_manager"]["network_name"], volumes=[])

        return container

    def __start_containers(self, containers):
        for container in containers:
            container.start()
            logger.info("Container started: {}".format(container.name))

    def run(self):
        logger.info("Started: {}".format(self.name))
        self.__clean_old()
        while not self.event.is_set():
            if len(self.dcli.containers.list(filters={"label": self.config["local_manager"]['label']})) == 0:
                self.containers = self.__initialize_containers()
                self.__start_containers(self.containers)
                self.event.wait(15)
            for container in self.containers:
                status = self.dcli.containers.get(container.id).status
                logger.info("Checking local container status: {} [{}]".format(container.name, status))
                if status not in ["running", "created"]:
                    logger.error("Local container {} is {}: restarting".format(container.name, status))
                    container.restart()
            self.event.wait(30)
        for container in self.containers:
            container.remove(force=True, v=True)
        self.containers = []
