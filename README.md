### Unofficial repository of [MonTreAL](http://dx.doi.org/10.1007/978-3-319-67008-9_52)

## Flow

**RPi (Sensor)**
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

```
