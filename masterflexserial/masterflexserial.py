"""Masterflex Serial Communication."""

import asyncio
import json
import logging
import serial
import serial_asyncio
import re
from masterflexserial.protocol import SerialProtocol, DIR

from masterflexserial.message import SentMessage
from masterflexserial.message import SentMessageType
from masterflexserial.message import SentMessageId
from masterflexserial.message import ReceivedMessage
from masterflexserial.message import create_message

logger = logging.getLogger(__name__)

# Pattern for matching a time string of the form "HH:MM:SS.s"
TIME_STRING_PATTERN = r"^\d{2}:\d{2}:\d{2}\.\d{1}$"


class MasterflexSerial:
    """Masterflex Serial CommunicationClient.

    Manages connection and auto-reconnection to the serial resource.
    """

    def __init__(self, port: str, _addr: str = '1', baud: float = 115200):
        """Initialize the Serial comm client.

        Args:
            port: Serial port to connect to.
            for examples:
                on Mac or Linux: /dev/hal/ttyUSB0
                on Windows     : COM1
            baud: serial comm baud rate default at 115200 bps
            _addr: serial address of the pump - default 1
        """

        self.port = port
        self._addr = "1"
        # Masterflex pump serial address support from 1 to 8 in text format
        if int(_addr) > 0 and int(_addr) < 9:
            self._addr = _addr

        self.baud_rate = baud
        self._recv_message = None
        self._data_event = asyncio.Event()

        # Get event loop in main thread
        self._loop = asyncio.get_event_loop()
        self._connect_task = None
        self._protocol = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """Connect to the serial port."""

        try:
            self._connect_task = await serial_asyncio.create_serial_connection(
                self._loop,
                self._protocol_factory,
                self.port,
                self.baud_rate)

        except serial.SerialException:
            self.logger.error('Unable to connect to: ', self.port)

    def disconnect(self):
        """Disconnect from the serial comm transport."""

        if self._connect_task and not self._connect_task.cancelled():
            # Cancel connection in progress.
            self._connect_task.cancel()
            self._connect_task = None

        if self._protocol and self._protocol.transport:
            # Close the serial transport.
            self.logger.debug('Close Serial connection to %s', self.port)
            self.protocol.transport.close()

    def _connection_lost(self):
        """Handle the connection lost."""
        self._protocol = None
        self.logger.error("Connection loss")

    def _connection_made(self,
                         protocol_connection: SerialProtocol):
        """Handle the connection being made.

        Args:
            protocol_connection: use SerialProtocol to make connection.
        """
        self.logger.info("connection to serial port", self.port, "is made")
        self._protocol = protocol_connection

    def _protocol_factory(self):
        """Create a protocol for the connection."""
        return SerialProtocol(
            self._connection_made,
            self._connection_lost,
            _resp_message=self._received_response_message
        )

    @property
    def connected(self):
        """Get the current serial connected state."""
        if self._protocol is not None and self._protocol.transport is not None:
            return True
        else:
            return False

    @property
    def protocol(self):
        """Return serial protocol."""
        return self._protocol

    @property
    def addr(self):
        """Get serial address."""
        return self._addr

    async def _send_message(self, msg: SentMessage, payload: str, addr: str = 1):
        """Write data to the serial port if it is open and connected.

        Args:
            msg: serial message to send to the pump and its type
            payload: message payload
            addr: address of the pump - default 1
        """
        if self.connected:
            self._data_event.clear()
            self._recv_message = None
            self._protocol.set_last_message(msg)
            data = create_message(msg, payload, addr)
            self._protocol.transport.write(data.encode())
            await self._data_event.wait()
            return self._recv_message.data

    def _received_response_message(self, recv_msg: ReceivedMessage):
        """Is called from a lower layer when a msg is decoded successfully.

        Args:
            recv_msg: received message from the pump
        """

        self._recv_message = recv_msg
        self._data_event.set()

    async def enable(self) -> json:
        """Enable serial communication mode on the pump.

        This message needs to be sent first before the pump can take serial command except
        set address command.

        Returns:
            - {"result": "OK"} for successful command
            - {"result": "Invalid"} for not a valid command
        """

        response = await self._send_message(
            SentMessage(SentMessageId.ENABLE, SentMessageType.RESP_SET), "1", self.addr)
        return response

    async def disable(self) -> json:
        """Disable serial communication mode on the pump.

        Returns:
            - {"result": "OK"} for successful command
            - {"result": "Invalid"} for not a valid command
        """

        return await self._send_message(
            SentMessage(SentMessageId.ENABLE, SentMessageType.RESP_SET), "0", self.addr)

    async def status(self) -> json:
        """Get the pump status.

        Returns:
            {"result": <string>, "address": <int>, "motor_status": <string>, "direction": <string>}
            {"result": <string>, "error": <string>}

            result: data, invalid
            address: 1-8
            motor_status: stopped, running
            direction: CW, CCW
            error: Invalid Type
            - Type: serial address, motor status, pump direction, etc.
        """

        return await self._send_message(
            SentMessage(SentMessageId.STATUS, SentMessageType.RESP_GET), None, self.addr)

    async def start(self) -> json:
        """Start the pump.

        Returns:
            - {"result": "OK"} for successful command
            - {"result": "Invalid"} for not a valid command
            - {"result": "Not in Serial Comms mode"} if the pump is not in Serial Comms mode
        """

        return await self._send_message(
            SentMessage(SentMessageId.START, SentMessageType.RESP_SET), None, self.addr)

    async def stop(self) -> json:
        """Stop the pump.

        Returns:
            - {"result": "OK"} for successful command
            - {"result": "Invalid"} for not a valid command
            - {"result": "Not in Serial Comms mode"} if the pump is not in Serial Comms mode
        """

        return await self._send_message(
            SentMessage(SentMessageId.STOP, SentMessageType.RESP_SET), None, self.addr)

    async def speed_percent(self, speed: float = None) -> json:
        """Set/Get the pump speed in percentage.

        Args:
            speed: - None: to get pump speed
                   - [0.0, 100.0]: to set the pump speed, accepting only 1 decimal point.

        Returns:
            - A json object for get pump speed
              {
                  "result": data,
                  "speed": value,
                  "unit": "%"
              }
            - Or {"result": "OK"} for successfully set pump speed
            - Or {"result": "Invalid", "error": "error message"} for invalid speed value

        """
        if (speed is None):
            return await self._send_message(
                SentMessage(SentMessageId.SPEEDP, SentMessageType.RESP_GET), None, self.addr)
        else:
            try:
                speed = float(speed)
                if 0 <= speed <= 100.0:
                    speed_str = "{:05}".format(round(speed * 10))
                    return await self._send_message(
                        SentMessage(SentMessageId.SPEEDP, SentMessageType.RESP_SET), speed_str, self.addr)
                else:
                    return {"result": "Invalid",
                            "error": "Speed in percent must be from 0 to 100"}
            except ValueError:
                return {"result": "Invalid",
                        "error": "Not a number. Speed in percent must be from 0 to 100"}

    async def set_dir(self, dir: None) -> json:
        """Set pumps direction.

        Args:
            dir: to SET pump's direction.
                 (e.g 'cw' or 'ccw')

        Returns:
            - {"result": "OK"} for successfully set direction.
            - Or {"result": "Invalid", "error": "Invalid param. Valid inputs: 'cw' or 'ccw'"}
              for invalid direction value.
        """

        if dir not in DIR.values():
            return {"result": "Invalid",
                    "error": "Invalid param. Valid inputs: 'cw' or 'ccw'"}

        else:
            if dir == 'cw':
                return await self._send_message(
                    SentMessage(SentMessageId.DIR_CW, SentMessageType.RESP_SET), None, self.addr)
            else:
                return await self._send_message(
                    SentMessage(SentMessageId.DIR_CCW, SentMessageType.RESP_SET), None, self.addr)

    async def reset_cumulative(self) -> json:
        """Reset cumulative volume in current unit set to zero-value.

        Returns:
            - {"result": "OK"} for successfully resetting cumulative volume
            - {"result": "Invalid"} for not a valid command
            - {"result": "Not in Serial Comms mode"} if the pump is not in Serial Comms mode
        """

        return await self._send_message(
            SentMessage(SentMessageId.RESET_CUMULATIVE, SentMessageType.RESP_SET), None, self.addr)

    async def set_addr(self, pump_addr) -> json:
        """Set pump address.

        Args:
            pump_addr: to SET pump's address [1-8].

        Returns:
            - {"result": "OK"} for successfully set address.
            - Or {"result": "Invalid", "error": "Address must be between 1 and 8"}
              for invalid number not between 1 and 8.
            - Or {"result": "Invalid", "error": "Not a valid number. Address must be integer between 1 and 8"}
              for decimal and not number value.
        """

        try:
            if 1 <= int(pump_addr) <= 8:
                self._addr = pump_addr
                return await self._send_message(
                    SentMessage(SentMessageId.SET_ADDR, SentMessageType.RESP_SET, "id"), pump_addr, self.addr)
            else:
                return {"result": "Invalid",
                        "error": "Address must be between 1 and 8"}
        except ValueError:
            return {"result": "Invalid",
                    "error": "Not a valid number. Address must be integer between 1 and 8"}

    async def speed_rpm(self, speed: float = None) -> json:
        """Set/Get the pump speed in rpm.

        Args:
            speed: - None: to GET pump speed in rpm.
                   - [min-rpm, max-rpm]: to SET the pump speed in rpm.
                   Please refer to the pump model for min-rpm and max-rpm.

        Returns:
            - A json object for get pump speed:
              {
                  "result": "data",
                  "speed": value,
                  "unit": "rpm"
              }
            - Or {"result": "OK"} for successfully set pump speed.
            - Or {"result": "Invalid", "error": "error message"} for invalid speed value.
        """

        if speed is None:
            return await self._send_message(
                SentMessage(SentMessageId.SPEEDR, SentMessageType.RESP_GET), None, self.addr)

        else:
            try:
                speed = float(speed)

                # Min and max to be modified in the future once pumps min and max can obtained.
                if 0 < speed <= 9999.99:
                    # Conversion to pass in correct payload value
                    payload = "{:06}".format(round(speed * 100))

                    return await self._send_message(
                        SentMessage(SentMessageId.SPEEDR, SentMessageType.RESP_SET), payload, self.addr)
                else:
                    return {"result": "Invalid",
                            "error": "Value out of range. Pumps range in RPM: 0 to 9999.99"}

            except ValueError:
                return {"result": "Invalid",
                        "error": "Invalid param. Valid inputs: int or float"}

    async def volume(self) -> json:
        """Get the pump volume in current unit set.

        Returns:
            - A json object for get pump volume:
              {
                  "result": "data",
                  "volume": value,
                  "unit": "unit"
              }
        """

        return await self._send_message(
            SentMessage(SentMessageId.VOLUME, SentMessageType.RESP_GET), None, self.addr)

    async def volume_rev(self) -> json:
        """Get the pump volume in rev.

        Returns:
            - A json object for get pump speed:
              {
                  "result": "data",
                  "volume": value,
                  "unit": "rev"
              }
        """

        return await self._send_message(
            SentMessage(SentMessageId.VOLUME_REV, SentMessageType.RESP_GET), None, self.addr)

    async def unit_index(self, index: int = None) -> json:
        """Set/Get the pump flow unit index.

        Args:
            index: - None: to GET pump flow unit index.
                   - [00, 32]: to SET the pump flow unit index.
                   Please refer to the pump model for index of flow units.

        Returns:
            - A json object for get pump flow unit index:
              {
                  "result": "data",
                  "index": value
              }
            - Or {"result": "OK"} for successfully set of flow unit index.
            - Or {"result": "Invalid", "error": "error message"} for invalid flow unit index value.
        """

        if index is None:
            return await self._send_message(
                SentMessage(SentMessageId.UNIT_INDEX, SentMessageType.RESP_GET), None, self.addr)

        else:
            try:
                index = int(index)
                # Min and max to be modified in the future once pumps min and max can obtained.
                if 0 < index <= 32:
                    # Conversion to pass in correct payload value
                    payload = "{:02}".format(index)

                    return await self._send_message(
                        SentMessage(SentMessageId.UNIT_INDEX, SentMessageType.RESP_SET), payload, self.addr)
                else:
                    return {"result": "Invalid",
                            "error": "Value out of range. Pumps flow unit index range: 0 to 32"}

            except ValueError:
                return {"result": "Invalid",
                        "error": "Invalid param. Valid inputs: integer"}

    async def on_time_full(self, time: str = None) -> json:
        """Set/Get the pump on-time in full.

        Args:
            - time: - None: to GET pump on-time in full.
                    - [00:00:00.1, 99:59:59.9]: to SET the pump on-time in full.
        Returns:
            - A json object for get pump on-time:
              {
               "result": "data",
               "on-time": value,
               "unit": "HH:MM:SS.X"
              }
            - Or {"result": "OK"} for successfully set of on-time.
            - Or {"result": "Invalid", "error": "error message"} for invalid on-time value.
        """

        if time is None:
            return await self._send_message(
                SentMessage(SentMessageId.ON_TIME_FULL, SentMessageType.RESP_GET), None, self.addr)

        if not isinstance(time, str):
            return {"result": "Invalid", "error": "Invalid param. Valid inputs: string"}

        if not re.match(TIME_STRING_PATTERN, time):
            return {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}

        try:
            # Split the time string into hours, minutes, seconds, and fractional
            hours, minutes, _decimal = time.split(":")
            seconds, fractional = _decimal.split(".")

            # Convert to total seconds
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            result = float(f"{total_seconds}.{fractional}")

            if not 0 < result <= 359999.9:
                return {"result": "Invalid", "error": "Time not within the range"}

            result = int(f"{hours}{minutes}{seconds}{fractional}")
            payload = "{:07}".format(result)

            return await self._send_message(
                SentMessage(SentMessageId.ON_TIME_FULL, SentMessageType.RESP_SET), payload, self.addr)
        except ValueError:
            return {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}

    async def set_panel_active(self, enable: bool) -> dict:
        """
        Set control panel to manual operation.

        Args:
            arg (bool): True to set to active, False to set to inactive.

        Returns:
            dict: JSON-like dictionary with the result of the command
        """

        if not isinstance(enable, bool):
            return {"result": "Invalid", "error": "Invalid param. Valid inputs: True or False"}

        command = SentMessageId.SET_PANEL_ACTIVE if enable else SentMessageId.SET_PANEL_INACTIVE

        return await self._send_message(
            SentMessage(command, SentMessageType.RESP_SET),
            None,
            self.addr
        )

    async def set_dispense_mode(self, mode: str) -> json:
        """Set pumps dispense mode.

        Args:
            mode: to SET pump's dispense mode.
                 (e.g 'continuous' or 'time')

        Returns:
            - {"result": "OK"} for successfully set mode.
            - Or {"result": "Invalid", "error": "Invalid param. Valid inputs: 'continuous' or 'time'"}
              for invalid direction value.
        """

        if mode == 'continuous':
            return await self._send_message(
                SentMessage(SentMessageId.SET_DISPENSE_CONTINUOUS, SentMessageType.RESP_SET), None, self.addr)
        elif mode == 'time':
            return await self._send_message(
                SentMessage(SentMessageId.SET_DISPENSE_TIME, SentMessageType.RESP_SET), None, self.addr)
        else:
            return {"result": "Invalid",
                    "error": "Invalid param. Valid inputs: 'continuous' or 'time'"}

    async def get_software_version(self):
        """Get the software version of the pump.

        Returns:
            {"result": <string>, "version": <string>}
            {"result": <string>, "error": <string>}
        """

        return await self._send_message(
            SentMessage(SentMessageId.GET_SOFTWARE_VERSION, SentMessageType.RESP_GET), None, self.addr)

    async def on_time_min(self, minutes: int) -> json:
        """Set the pump on time in minutes.

        Args:
            minutes: - [0, 999]: the value set to be the on time in minutes.

        Returns:
            - {"result": "OK"} for successfully set of flow unit index.
            - Or {"result": "Invalid", "error": "error message"} for invalid flow unit index value.
        """

        if not isinstance(minutes, str) and not isinstance(minutes, int):
            return {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}

        try:
            minutes = int(minutes)
            if 1 <= minutes <= 999:
                # Conversion to pass in correct payload value
                payload = "{:03}".format(minutes)

                return await self._send_message(
                    SentMessage(SentMessageId.SET_ON_TIME_MIN, SentMessageType.RESP_SET), payload, self.addr)
            else:
                return {"result": "Invalid",
                        "error": "Value out of range. Pumps flow unit index range: 1 to 999"}
        except ValueError:
            return {"result": "Invalid",
                    "error": "Invalid param. Valid inputs: integer"}

    async def on_time_hr(self, hours: int) -> json:
        """Set the pump on time in hours.

        Args:
            hours: - [0, 99]: the value set to be the on time in hours.
        Returns:
            - {"result": "OK"} for successfully set of on time in hours.
            - Or {"result": "Invalid", "error": "error message"} for invalid time value.
        """

        if not isinstance(hours, str) and not isinstance(hours, int):
            return {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}

        try:
            hours = int(hours)
            if 1 <= hours <= 99:
                # Conversion to pass in correct payload value
                payload = "{:02}".format(hours)

                return await self._send_message(
                    SentMessage(SentMessageId.SET_ON_TIME_HR, SentMessageType.RESP_SET), payload, self.addr)
            else:
                return {"result": "Invalid",
                        "error": "Value out of range. On Time hour range: 1 to 99"}
        except ValueError:
            return {"result": "Invalid",
                    "error": "Invalid param. Valid inputs: integer"}

    async def get_version__model(self) -> json:
        """Get the pump software version and model.

        Returns:
            {"result": "data", "Model": <string>, "SerialComm Version": <int>}
            {"result": <string>, "error": <string>}
        """

        return await self._send_message(
            SentMessage(SentMessageId.MODEL_AND_VERSION, SentMessageType.RESP_GET), None, self.addr)

    async def store_configs(self) -> dict:
        """Store the current pump configurations.

        Returns:
            dict: JSON-like dictionary with the result of the command.
                - {"result": "OK"} if the command is successful.
                - {"result": "Error", "error": "Error message"} for failures.
        """
        return await self._send_message(
            SentMessage(SentMessageId.STORE_CONFIGS, SentMessageType.RESP_SET),
            None,
            self.addr
        )

    async def restore_configs(self) -> dict:
        """
        Restores the pump configurations to the default state.

        Returns:
            dict: JSON-like dictionary with the result of the command.
                - {"result": "OK"} if the command is successful.
                - {"result": "Error", "error": "Error message"} for failures.
        """
        return await self._send_message(
            SentMessage(SentMessageId.RESTORE_CONFIGS, SentMessageType.RESP_SET),
            None,
            self.addr
        )

    async def reset_batch(self) -> json:
        """Reset batch count set to zero-value.

        Returns:
            - {"result": "OK"} for successfully resetting batch count
            - {"result": "Invalid"} for not a valid command
            - {"result": "Not in Serial Comms mode"} if the pump is not in Serial Comms mode
        """

        return await self._send_message(
            SentMessage(SentMessageId.RESET_BATCH_COUNT, SentMessageType.RESP_SET), None, self.addr)

    async def dispense_status(self) -> json:
        """Get the pump dispense status.

        Returns:
            {"result": "data", "status": <string>}
            {"result": <string>, "error": <string>}
        """

        return await self._send_message(
            SentMessage(SentMessageId.DISPENSE_STATUS, SentMessageType.RESP_GET), None, self.addr)

    async def off_time_full(self, time: str = None) -> json:
        """Set/Get the pump off-time in full.

        Args:
            - time: - None: to GET pump off-time in full.
                    - [00:00:00.1, 99:59:59.9]: to SET the pump off-time in full.
        Returns:
            - A json object for get pump off-time:
              {
               "result": "data",
               "off-time": value,
               "unit": "HH:MM:SS.X"
              }
            - Or {"result": "OK"} for successfully set of off-time.
            - Or {"result": "Invalid", "error": "error message"} for invalid off-time value.
        """

        if time is None:
            return await self._send_message(
                SentMessage(SentMessageId.OFF_TIME_FULL, SentMessageType.RESP_GET), None, self.addr)

        if not isinstance(time, str):
            return {"result": "Invalid", "error": "Invalid param. Valid inputs: string"}

        if not re.match(TIME_STRING_PATTERN, time):
            return {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}

        try:
            # Split the time string into hours, minutes, seconds, and fractional
            hours, minutes, _decimal = time.split(":")
            seconds, fractional = _decimal.split(".")

            # Convert to total seconds
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            result = int(f"{total_seconds}{fractional}")

            if not 0 < result <= 3599999:
                return {"result": "Invalid", "error": "Time not within the range"}

            result = int(f"{hours}{minutes}{seconds}{fractional}")
            payload = "{:07}".format(result)

            return await self._send_message(
                SentMessage(SentMessageId.OFF_TIME_FULL, SentMessageType.RESP_SET), payload, self.addr)
        except ValueError:
            return {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}

    async def on_time_decisecond(self, deciseconds: int = None) -> json:
        """Set/Get the pump on-time in 1/10 seconds.

        Args:
            - deciseconds: - None: to GET pump on-time in 1/10 seconds.
                    - [0, 9999]: to SET the pump on-time in 1/10 seconds.
        Returns:
            - A json object for get pump on-time:
              {
               "result": "data",
               "on-time": value,
               "unit": "1/10 sec"
              }
            - Or {"result": "OK"} for successfully set of on-time.
            - Or {"result": "Invalid", "error": "error message"} for invalid on-time value.
        """

        if deciseconds is None:
            return await self._send_message(
                SentMessage(SentMessageId.ON_TIME_DECISEC, SentMessageType.RESP_GET), None, self.addr)

        if not isinstance(deciseconds, str) and not isinstance(deciseconds, int):
            return {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}

        try:
            deciseconds = int(deciseconds)  # Convert to integer
            if 1 <= deciseconds <= 9999:
                # Conversion to pass in correct payload value
                payload = "{:04}".format(deciseconds)

                return await self._send_message(
                    SentMessage(SentMessageId.ON_TIME_DECISEC, SentMessageType.RESP_SET), payload, self.addr)
            else:
                return {"result": "Invalid",
                        "error": "Value out of range. Pumps on time deciseconds range: 0 to 9999"}
        except ValueError:
            return {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}

    async def batch_count(self, batch_count: int = None) -> dict:
        """Get/Set the pump's Batch Total.

        Args:
            batch_count:
                - None: Get batch count
                - [0, 99999]: Integer value representing the Batch Total to set.

        Returns:
            dict:
                JSON-formatted response from the pump
                {
                    "result": "data",
                    "count": count,
                    "total": total
                }
            - Or {"result": "OK"} for successfully set of batch count.
            - Or {"result": "Invalid", "error": "error message"} for invalid batch count value.
        """

        if batch_count is None:
            return await self._send_message(
                SentMessage(SentMessageId.BATCH_COUNT, SentMessageType.RESP_GET), None, self.addr)

        def is_valid_integer(value: str) -> bool:
            if value.startswith("-"):  # Handle negatives
                return value[1:].isdigit()  # Check digits after the '-'
            return value.isdigit()  # For positive numbers

        if not is_valid_integer(str(batch_count)):
            return {"result": "Invalid", "error": "Not an integer"}

        batch_count = int(batch_count)
        if not (0 <= batch_count <= 99999):
            return {"result": "Invalid", "error": "Value must be between 0 and 99999"}

        # Create payload with zero-padded 5-digit value
        payload = "{:05}".format(batch_count)
        # Send the command to the pump
        return await self._send_message(
            SentMessage(SentMessageId.BATCH_COUNT, SentMessageType.RESP_SET), payload, self.addr)
