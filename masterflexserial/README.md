# MasterflexSerial Class

Masterflex Serial Communication Client - please refer to sample code(s) in `Console` folder for utilization.



## `def __init__()`

Initialize the Serial comm client.

**Args:**
```
    port: Serial port to connect to.
    for examples:
        on Mac or Linux: /dev/hal/ttyUSB0
        on Windows     : COM1
    baud: serial comm baud rate default at 115200 bps
    _addr: serial address of the pump - default 1
```

## `async def connect()`

Connect to the serial port.

## `async def disconnect()`

Disconnect from the serial comm transport.

## `async def connected()`

Get the current serial connected state.

## `async def addr()`

Get serial address.

## `async def enable()`

Enable serial communication mode on the pump.

This message needs to be sent first before the pump can take serial command except
set address command.


**Returns:**

    - {"result": "OK"} for successful command
    - {"result": "Invalid"} for not a valid command


## `async def disable()`

Disable serial communication mode on the pump.

**Returns:**

    - {"result": "OK"} for successful command
    - {"result": "Invalid"} for not a valid command


## `async def status()`

Get the pump status.

**Returns:**

    - {"result": <string>, "address": <int>, "motor_status": <string>, "direction": <string>}
    - {"result": <string>, "error": <string>}

    - result: data, invalid
    - address: 1-8
    - motor_status: stopped, running
    - direction: CW, CCW
    - error: Invalid <Type>
        - Type: serial address, motor status, pump direction, etc.


## `async def start()`

Start the pump.

**Returns:**

    - {"result": "OK"} for successful command
    - {"result": "Invalid"} for not a valid command
    - {"result": "Not in Serial Comms mode"} if the pump is not in Serial Comms mode


## `async def stop()`

Stop the pump.

**Returns:**

    - {"result": "OK"} for successful command
    - {"result": "Invalid"} for not a valid command
    - {"result": "Not in Serial Comms mode"} if the pump is not in Serial Comms mode


## `async def speed_percent(speed: float = None)`

Set/Get the pump speed in percentage.

**Args:**

    - speed: - None: to get pump speed
    - [0.0, 100.0]: to set the pump speed, accepting only 1 decimal point.


**Returns:**

    - A json object for get pump speed
      {
          "result": data,
          "speed": value,
          "unit": "%"
      }
    - Or {"result": "OK"} for successfully set pump speed
    - Or {"result": "Invalid", "error": "error message"} for invalid speed value


## `async def set_dir(dir: None)`

Set pumps direction.

**Args:**

    - dir: to SET pump's direction.
         (e.g 'cw' or 'ccw')


**Returns:**

    - {"result": "OK"} for successfully set direction.
    - Or {"result": "Invalid", "error": "Invalid param. Valid inputs: 'cw' or 'ccw'"}
      for invalid direction value.


## `async def reset_cumulative()`

Reset cumulative volume in current unit set to zero-value.

**Returns:**

    - {"result": "OK"} for successfully resetting cumulative volume
    - {"result": "Invalid"} for not a valid command
    - {"result": "Not in Serial Comms mode"} if the pump is not in Serial Comms mode


## `async def set_addr(pump_addr)`

Set pump address.

**Args:**

    - pump_addr: to SET pump's address [1-8].


**Returns:**

    - {"result": "OK"} for successfully set address.
    - Or {"result": "Invalid", "error": "Address must be between 1 and 8"}
      for invalid number not between 1 and 8.
    - Or {"result": "Invalid", "error": "Not a valid number. Address must be integer between 1 and 8"}
      for decimal and not number value.


## `async def speed_rpm(speed: float = None)`

Set/Get the pump speed in rpm.

**Args:**

    - speed: - None: to GET pump speed in rpm.
           - [min-rpm, max-rpm]: to SET the pump speed in rpm.
           Please refer to the pump model for min-rpm and max-rpm.


**Returns:**

    - A json object for get pump speed:
      {
          "result": "data",
          "speed": value,
          "unit": "rpm"
      }
    - Or {"result": "OK"} for successfully set pump speed.
    - Or {"result": "Invalid", "error": "error message"} for invalid speed value.


## `async def volume()`

Get the pump volume in current unit set.

**Returns:**

    - A json object for get pump volume:
      {
          "result": "data",
          "volume": value,
          "unit": "unit"
      }


## `async def volume_rev()`

Get the pump volume in rev.

**Returns:**

    - A json object for get pump speed:
      {
          "result": "data",
          "volume": value,
          "unit": "rev"
      }


## `async def unit_index(speed: float = None)`

Set/Get the pump flow unit index.

**Args:**

    - index: - None: to GET pump flow unit index.
    - [00, 32]: to SET the pump flow unit index.
    Please refer to the pump model for index of flow units.


**Returns:**

    - A json object for get pump flow unit index:
      {
          "result": "data",
          "index": value
      }
    - Or {"result": "OK"} for successfully set of flow unit index.
    - Or {"result": "Invalid", "error": "error message"} for invalid flow unit index value.

