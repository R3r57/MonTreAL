import json
import os


class ConfigurationReader:

    def get():
        configuration = os.environ['CONFIG']
        if os.path.isfile(configuration):
            with open(configuration, "r") as file:
                config = json.load(file)
                return config
        else:
            print(configuration)
            # temporary fix
            config = json.loads(configuration.replace("True", "true").replace("False", "false").replace("\'", "\""))
            return config
