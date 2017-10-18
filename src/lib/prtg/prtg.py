#!/usr/bin/env python3

import json


class PRTG:

    def __init__(self):
        self.data = {"prtg": {"text": "", "result": []}}

    def set_text(self, message):
        self.data["prtg"]["text"] = str(message)

    def add_channel(self, name, value, unit):
        channel = {}
        channel["float"] = "1"
        channel["unit"] = "custom"
        channel["channel"] = name
        channel["value"] = value
        channel["customunit"] = unit
        self.data["prtg"]["result"].append(channel)

    def get_json(self):
        return self.data

    def print_json(self):
        print(json.dumps(self.data, indent=2))


if __name__ == '__main__':
    paessler = prtg()
    paessler.set_text("Hello World")
    paessler.add_channel("humidity", 50, "percent")
    paessler.print_json()
