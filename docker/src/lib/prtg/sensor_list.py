import io
import requests
import json
import threading
from multiprocessing import Queue


class SensorList (threading.Thread):
    def __init__(self, name, event, queue, url="http://info.staging.ub.uni-bamberg.de"):
        threading.Thread.__init__(self)
        self.prefixes = ["json","prtg"]
        self.weburl = "http://prtg.pisensor.ub.uni-bamberg.de"
        self.name = name
        self.event = event
        self.queue = queue
        self.url = url

    def run(self):
        print("Starting " + self.name)
        while not self.event.is_set():
            self.event.wait(5)
            new_data=[]
            while not self.queue.empty():
                data = json.loads(self.queue.get().replace("'", '"'))
                new_data.append(data)
            for prefix in self.prefixes:
                self.create_list(new_data, prefix)
            self.event.wait(300)
        print("stop", self.name)

    def create_list(self,data,prefix):
        new_data=[]
        for i in data:
            new_data.append("{}/{}/{}_{}/{}".format(
                                                    self.weburl,
                                                    prefix,
                                                    i["hostname"],
                                                    i["machine_id"],
                                                    str(i["sensor_id"])))

        filename = "{}.json".format(prefix)
        data=list(set(new_data))
        data.sort()
        self.send_list(data,filename)

    def send_list(self, data, fname="hello.txt"):
        text = "\n".join(data)
        with io.StringIO(text) as f:
            r = requests.post(self.url + "/upload", files={fname: f})
        return (r.status_code, r.text)

    def get_list(self,fname="hello.txt"):
        g = requests.get(self.url + "/sensors" + fname ,stream=True)
        if g.status_code == 200:
            return g.text.split("\n")
        else:
            return None
