### Unofficial repository of [MonTreAL](http://dx.doi.org/10.1007/978-3-319-67008-9_52)

## Flow

**RPi (Sensor)**
```
                           o- NsqReader - InfluxDBWriter - InfluxDB -o- Chronograf
        USB                |                                         |
         |                 o- NsqReader - ...                        o- Grafana
       Sensor              |
         |                 o- NsqReader - SensorList -o             o- Rest
    SocketWriter           |                          |             |
         |                 o- NsqReader - SensorData -o- memcached -o- ...
        [|]                |                                        |
         |                 o- NsqAdmin, NsqCli, etc.                o- ...
    SocketReader           |
         |                 |\
  MetaDataAppender         | NsqLookup
         |                 |/
      NsqWriter --------- Nsq

```
