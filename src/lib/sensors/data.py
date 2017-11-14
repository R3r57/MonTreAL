import json

class Measurement:
    def __init__(self, id, type, temp, hum):
        temperature = {"name": "temperature", "value": float(temp), "unit": "°C"}
        humidity = {"name": "humidity", "value": float(hum), "unit": "%"}
        measurements = [temperature, humidity]
        self.data = {"sensor_id": id, "type": type, "measurements": measurements}

    def get_data(self):
        return self.data

    def to_json(self):
        return json.dumps(self.data)

    def __str__(self):
        return self.to_json()
