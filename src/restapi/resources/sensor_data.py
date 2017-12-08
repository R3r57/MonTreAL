from flask_restful import Resource

class SensorData(Resource):
    def __init__(self, memcache_client):
        Resource.__init__(self)
        self.memcache_client = memcache_client

    def get(self, prefix, device_id, sensor, sensor_id):
        data = self.memcache_client.read("{}{}{}{}".format(str(prefix), str(device_id), str(sensor), str(sensor_id)))
        return data
