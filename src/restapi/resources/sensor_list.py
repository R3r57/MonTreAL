from flask_restful import Resource

class SensorList(Resource):
    def __init__(self, memcache_client):
        super(SensorList, self).__init__()
        self.memcache_client = memcache_client

    def get(self, prefix):
        data = self.memcache_client.read("{}sensorlist".format(prefix))
        return data