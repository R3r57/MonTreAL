### Unofficial repository of [MonTreAL](http://dx.doi.org/10.1007/978-3-319-67008-9_52)

## Flow

**RPi (Sensor)**
```
     USB (USB-WDE1)
      |
    Sensor (ASH2200)
      |                           |
      SocketWriter                |
      |                           |
     <|>                          |- NsqCli
      |                           |
      SocketReader                |- NsqAdmin
      |                           |
      MetaDataAppender            NsqLookup
      |                           |
      NsqWriter ----------------- Nsq
```
