import json, time

class SensorData:
    def __init__(self, hostname, machine_id, room, library, data):
        self.data = json.loads(data.replace("'", '"'))
        self.data.update({"hostname": hostname,
                          "machine_id": machine_id,
                          "room": room,
                          "library": library,
                          "timestamp": int(time.time())})

    def to_json(self):
        return json.dumps(self.data)

    def __str__(self):
        return self.to_json()
