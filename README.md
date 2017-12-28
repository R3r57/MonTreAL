# Environmental Monitoring of Libraries with [MonTreAL](http://dx.doi.org/10.1007/978-3-319-67008-9_52)

[![Build Status](https://travis-ci.org/R3r57/MonTreAL.dockerimagebuilder.svg?branch=master)](https://travis-ci.org/R3r57/MonTreAL.dockerimagebuilder)
[![Docker Stars](https://img.shields.io/docker/stars/r3r57/montreal.svg)](https://hub.docker.com/r/r3r57/montreal/)
[![Docker Pulls](https://img.shields.io/docker/pulls/r3r57/montreal.svg)](https://hub.docker.com/r/r3r57/montreal/)

[Docker Image Builder](https://github.com/r3r57/MonTreAL_docker-image-builder)
| [Docker Swarm Setup](https://github.com/r3r57/MonTreAL_swarm-setup)
| [VM Image Builder](https://github.com/r3r57/MonTreAL_vm-image-builder)

An ever-increasing amount of devices connected over the Internet pave the road towards the realization of the ‘Internet of Things’ (IoT) idea. With IoT, endangered infrastructures can easily be enriched with low-cost, energy-efficient monitoring solutions, thus alerting is possible before severe damage occurs. We developed a library wide humidity and temperature monitoring framework MonTreAL, which runs on commodity single board computers. In addition, our primary objectives are to enable flexible data collection among a computing cluster by migrating virtualization approaches of data centers to IoT infrastructures.

We evaluate our prototype of the system MonTreAL at the University Library of Bamberg by collecting temperature and humidity data.


## Flow

```
                           o- NsqReader - InfluxDBWriter   - InfluxDB   -o- Chronograf, (Kapacitor)
                           |                                              \
                           |                                               o- Grafana
        USB                |                                              /
         |                 o- NsqReader - PrometheusWriter - Prometheus -o- (Alertmanager)
       Sensor              |
         |                 o- NsqReader - SensorList -o
    SocketWriter           |                          |- memcached - Web
         |                 o- NsqReader - SensorData -o
        [|]                |
         |                 o- NsqAdmin, NsqCli, etc.
    SocketReader           |
         |                 |\
  MetaDataAppender         | NsqLookup
         |                 |/
      NsqWriter --------- Nsq

                                                        (____): not implemented yet
```

## Sensor Configuration

### Temperature And Humidity

#### Sensor Mock
    "mock": {
      "service": "temperature_humidity_sensor",
      "type": "mock",
      "image": "r3r57/montreal:latest-multiarch",
      "device": [],
      "command": "",
      "configuration": {
        "sensor_count": <int>,
        "temperature": <float>,
        "humidity": <float>,
        "interval": <int>
      }
    }

#### [ASH2200](https://www.elv.de/elv-funk-aussensensor-ash-2200-fuer-z-b-usb-wde-1-ipwe-1.html)
    "ash2200": {
      "service": "temperature_humidity_sensor",
      "type": "ash2200",
      "image": "r3r57/montreal:latest-multiarch",
      "device": ["/dev/ttyUSB0"],
      "command": "",
      "configuration": {
        "device": "/dev/ttyUSB0",
        "baudrate": "9600",
        "timeout": <int>
      }
    }

#### [DHT11/DHT22/AM2302](https://learn.adafruit.com/dht/overview)
    "dht": {
      "service": "temperature_humidity_sensor",
      "type": "dht",
      "image": "r3r57/montreal:latest-multiarch",
      "devices": ["/dev/mem"],
      "command": "",
      "configuration": {
        "id": <int>,
        "gpio": <int>,
        "short_type": <11 or 22>,
        "interval": <int>
      }
    }

#### [OpenWatherMap](https://openweathermap.org/)
    "open_weather_map": {
      "service": "temperature_humidity_sensor",
      "type": "openweathermap",
      "image": "r3r57/montreal:latest-multiarch",
      "devices": [],
      "command": "",
      "configuration": {
        "id": <int>,
        "key": <string>,
        "city": <string>,
        "country": <string>,
        "interval": <int>
      }
    }
