import json
import time


class SensorData:
    def __init__(self, hostname, device_id, building, room, data):
        self.data = json.loads(data.replace("'", '"'))
        self.data.update({"hostname": hostname,
                          "device_id": device_id,
                          "building": building,
                          "room": room,
                          "timestamp": int(time.time())})

    def to_json(self):
        return json.dumps(self.data)

    def __str__(self):
        return self.to_json()
