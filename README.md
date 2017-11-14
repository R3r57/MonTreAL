# Environmental Monitoring of Libraries with [MonTreAL](http://dx.doi.org/10.1007/978-3-319-67008-9_52)

[![BuildStatus](https://travis-ci.org/r3r57/MonTreAL_docker-image-builder.svg?branch=master)](https://travis-ci.org/r3r57/MonTreAL_docker-image-builder)
[![Docker Stars](https://img.shields.io/docker/stars/r3r57/montreal.svg)](https://hub.docker.com/r/r3r57/montreal/)
[![Docker Pulls](https://img.shields.io/docker/pulls/r3r57/montreal.svg)](https://hub.docker.com/r/r3r57/montreal/)

## Flow

```
                           o- NsqReader - InfluxDBWriter   - InfluxDB   -o- Chronograf, (Kapacitor)
                           |                                              \
                           |                                               o- Grafana
        USB                |                                              /
         |                 o- NsqReader - PrometheusWriter - Prometheus -o- (Alertmanager)
       Sensor              |
         |                 o- NsqReader - SensorList -o
    SocketWriter           |                          |- memcached - Rest
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
