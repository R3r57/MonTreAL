#!/usr/bin/env python3

import urllib
import re
import requests
import ast


class PRTGError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class prtg_sensor():

    """docstring for prtg_sensor."""
    def __init__(self,
                 nodename="",
                 room="",
                 description="None",
                 url="",
                 location="TB3",
                 sensor_id="",
                 base_url="https://prtg.rz.uni-bamberg.de",
                 username=None,
                 passhash=None):

        self.ids = {"TB1": "41484", "TB3": "40128", "TB4": "41492", "TB5": "41496"}
        self.location = location
        self.desc = self.__create_description(nodename, room, description)
        self.room = room
        self.url = url
        self.device_id = self.__get_id(location)
        self.parent_id = "41344"
        self.group_id = "40123"
        self.base_url = self.__check_url(base_url)
        self.running = False
        self.identifier = None
        self.sensor_id = sensor_id

        if passhash is not None and passhash != "":
            self.passhash = passhash
        else:
            self.passhash = "passhash"

        if username is not None and username != "":
            self.username = username
        else:
            self.username = "username"

###########
# private #
###########

    def __create_description(self, nodename, room, description):
        if description is None or description == "":
            if nodename is not None and nodename != "" and room is not None and room != "":
                return nodename + " | " + room
            else:
                raise PRTGError('Description, Nodename and Room are not allowed to be empty at the same time!')
        elif description is not None and description != "":
            return description
        else:
            raise PRTGError('Description, Nodename and Room are not allowed to be empty at the same time!')

    def __get_id(self, location):
        if location in self.ids:
            return self.ids[location]
        else:
            raise PRTGError('Es gibt keinen Ort ' + location)

    def __insert_sensor(self, description, url, sensor_id, location, running, identifier, username, passhash):
        self.identifier = identifier
        self.url = url
        self.desc = description
        self.location = location
        self.running = running
        self.username = username
        self.passhash = passhash
        self.device_id = self.__get_id(location)
        self.sensor_id = sensor_id

    def __check_url(self, url):
        if url.endswith("/"):
            return url[:-1]
        else:
            return url

    def __call_url(self, url, **args):
        args.update({'username': self.username, 'passhash': self.passhash})
        reply = requests.get(url, args, allow_redirects=False)
        if reply.status_code == 302:
            return {'Code': 302, 'Reply': reply.headers['Location']}
        elif reply.status_code == 200:
            return {'Code': 200, 'Reply': reply.text}
        else:
            print("#######################\nError:")
            print({'Code': reply.status_code,
                   'Text': reply.text,
                   'Header': reply.headers})
            raise PRTGError("HTTP-Error " + str(reply.status_code) + " has occurred")

    def __parse_url(self, url):
        list_url = re.split('\?|\&', url)
        reply = None
        for s in list_url:
            if s.startswith("id"):
                reply = s.split('=')[1]
                break
        return reply

    def __get_sensors(self, *args):
        url = self.base_url + "/api/table.json"
        reply = self.__call_url(url,
                                id=self.group_id,
                                content="sensors",
                                columns=','.join(args))
        d = ast.literal_eval(reply['Reply'])
        if "sensors" in d:
            return d['sensors']
        else:
            return None

    def __var_in_list(self, liste, prop, value):
        for x in liste:
            if x[prop] == value:
                return True
        return False

##########
# public #
##########

    def create_sensor(self, force=False):
        if self.identifier is None or self.identifier == "" or force:
            url = self.base_url + "/api/duplicateobject.htm"
            reply = self.__call_url(url,
                                    id=self.parent_id,
                                    name=self.desc,
                                    targetid=self.device_id)
            if reply['Code'] == 302:
                self.identifier = self.__parse_url(reply['Reply'])
                self.running = False
                return True
            else:
                return False
        else:
            raise PRTGError("Sensor-Id already exists (possibly Sensor exists, too). Use 'force=True' to override it")
            return False

    def set_property(self, prop="httpurl", value="www.uni-bamberg.de"):  # name,httpurl
        url = self.base_url + "/api/setobjectproperty.htm"
        reply = self.__call_url(url, id=self.identifier, name=prop, value=value)
        if reply['Code'] == 200:
            return True
        else:
            return False

    def get_data(self):
        ret = {'Name': self.desc,
               'Device-ID': self.device_id,
               'Running': self.running,
               'Location': self.location,
               'Parent-ID': self.parent_id,
               'Sensor-ID': self.sensor_id,
               'URL': self.url}
        if self.identifier is not None and self.identifier != "":
            ret.update({'ID': self.identifier})
        return ret

    def set_running(self, new_state):
        if self.running != new_state:
            url = self.base_url + "/api/pause.htm"
            reply = self.__call_url(url,
                                    id=self.identifier,
                                    action=int(new_state))
            if reply['Code'] == 200:
                return True
            else:
                return False
        else:
            return False

    def set_url(self):
        return self.set_property(prop="httpurl", value=self.url)

########################################################


class prtg_api():
    def __init__(self, username=None, passhash=None):
        self.sensors = []
        self.locations = {"41484": "TB1",
                          "41488": "TB2",
                          "40128": "TB3",
                          "41492": "TB4",
                          "41496": "TB5",
                          "41500": "ERBA"}
        self.base_url = "https://prtg.rz.uni-bamberg.de"
        self.group_id = "40123"
        self.username = username
        self.passhash = passhash

###########
# private #
###########

    def __call_url(self, url, **args):
        args.update({'username': self.username, 'passhash': self.passhash})
        reply = requests.get(url, args, allow_redirects=False)
        if reply.status_code == 302:
            return {'Code': 302, 'Reply': reply.headers['Location']}
        elif reply.status_code == 200:
            return {'Code': 200, 'Reply': reply.text}
        else:
            print("#######################\nError:")
            print({'Code': reply.status_code,
                   'Text': reply.text,
                   'Header': reply.headers})
            raise PRTGError("HTTP-Error " + str(reply.status_code) + " has occurred")

    def __get_sensors(self, *args):
        url = self.base_url + "/api/table.json"
        reply = self.__call_url(url,
                                id=self.group_id,
                                content="sensors",
                                columns=','.join(args))
        d = ast.literal_eval(reply['Reply'])
        if "sensors" in d:
            return d['sensors']
        else:
            return None

    def __sensor_exists(self, sensor_data):
        for data in self.sensors:
            d = data.get_data()
            matches = 0
            for key in sensor_data:
                if key in d and d[key] == sensor_data[key]:
                    matches += 1
            if matches == len(sensor_data):
                return True
        return False

    def __add_existing_sensor(self, sensor):
        self.sensors.append(sensor)

    def __get_location(self, parent_id):
        return self.locations[parent_id]

    def __dict_in_dictlist(self, s_dict, dictlist):
        for d in dictlist:
            matches = 0
            for key in s_dict:
                if key in d and d[key] == s_dict[key]:
                    matches += 1
            if matches == len(s_dict):
                return True
        return False

##########
# public #
##########

    def add_sensor(self,
                   nodename="",
                   room="",
                   location="",
                   description=None,
                   sensor_id="",
                   url=""):
        sensor = prtg_sensor(nodename=nodename,
                             room=room,
                             location=location,
                             description=description,
                             url=url,
                             sensor_id=sensor_id,
                             username=self.username,
                             passhash=self.passhash)
        search = sensor.get_data().copy()
        search.pop("Running", None)

        if not self.__sensor_exists(search):
            sensor.create_sensor()
            sensor.set_url()
            print("Add Sensor: Sensor '{}' added".format(sensor.get_data()['Name']))
            was_started = sensor.set_running(True)
            self.__add_existing_sensor(sensor)
            print("Start Sensor: Sensor '{}' {} started".format(sensor.get_data()['Name'], "was" if was_started else "wasn't"))
            return True
        else:
            print("Add Sensor: Sensor '{}' already exists".format(sensor.get_data()['Name']))
            return False

    def add_sensor_list(self, liste):
        if liste is None or len(liste) <= 0:
            raise PRTGError("No empty Lists/Tuples allowed")

        for item in liste:
            if item is None or item == {} or not isinstance(item, dict):
                raise PRTGError("No empty and none-dict items allowed")
            nodename = item['NAME'] if 'NAME' in item else ""
            room = item['ROOM'] if 'ROOM' in item else ""
            location = item['LOCAL'] if 'LOCAL' in item else ""
            description = item['DESC'] if 'DESC' in item else None
            identifier = item['ID'] if 'ID' in item else None

            self.add_sensor(nodename=nodename,
                            room=room,
                            location=location,
                            description=description,
                            identifier=identifier)

    def get_data(self, typ="list"):
        if typ != "list" and typ != "tuple":
            raise PRTGError("'" + typ + "' is not supported. Use 'list' or 'tuple' instead")
        data = []
        for sensor in self.sensors:
            data.append(sensor.get_data())
        if typ == "tuple":
            data = tuple(data)
        return data

    def create_all_sensors(self, force=False):
        for sensor in self.sensors:
            if sensor.get_data()['ID'] is not None or force:
                print("Creating '" + sensor.get_data()['Name'] + "'")
                try:
                    sensor.create_sensor(force)
                    print("Sensor created")
                except e:
                    print("Action failed")
            else:
                print("Skipping '" + sensor.get_data()['Name'] + "'")

    def get_prtg_sensors(self):
        sensors = []
        new_sensors = []
        print("Get PRTG-Sensors")
        sensors = self.__get_sensors("objid", "parentid", "name", "info")
        for sensor in sensors:
            sensor['objid'] = str(sensor['objid'])
            sensor['parentid'] = str(sensor['parentid'])
            # Name~SensorID~MachineID
            name = sensor['name'].split("~")
            sensor['url'] = ""
            sensor['sensorid'] = ""
            if len(name) > 1:
                sensor['sensorid'] = name[1]
            if len(name) > 2:
                sensor['url'] = "/prtg/{}_{}/{}".format(name[0],
                                                        name[2],
                                                        name[1])
            new_sensor = prtg_sensor()
            new_sensor._prtg_sensor__insert_sensor(sensor['name'],
                                                   sensor['url'],
                                                   sensor['sensorid'],
                                                   self.__get_location(sensor['parentid']),
                                                   ("paused" not in sensor['info']),
                                                   sensor['objid'],
                                                   self.username,
                                                   self.passhash)
            new_sensors.append(new_sensor)
        if new_sensors is not None:
            print("Reseting sensor list")
            self.sensors.clear()
            self.sensors = new_sensors.copy()

    def set_running_all(self, new_state):
        for sensor in self.sensors:
            sensor.set_running(new_state)
