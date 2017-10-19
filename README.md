### Unofficial repository of [MonTreAL](http://dx.doi.org/10.1007/978-3-319-67008-9_52)

## Flow

**RPi (Sensor)**
```
                                     o- ...
        USB                          |
         |                           o- NsqReader
       Sensor                        |
         |                           o- NsqReader
    SocketWriter                     |
         |                           o- NsqReader
        [|]                          |
         |                           o- NsqAdmin, NsqCli, etc.
    SocketReader                     |
         |                           |\
  MetaDataAppender                   | NsqLookup
         |                           |/
      NsqWriter ------------------- Nsq

```
