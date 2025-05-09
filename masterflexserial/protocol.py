"""The module includes two classes SerialProtocol and Decoder.

Decoder: The responded message from the pump.
SerialProtocol: Response to the serial message and call the Decoder class.
"""
import asyncio
import logging

from masterflexserial.message import SentMessageType, SentMessage, ReceivedMessageId, ReceivedMessage, SentMessageId

logger = logging.getLogger(__name__)


MOTOR_STATUS = {
    "0": "stopped",
    "1": "running"
}

DIR = {
    "0": "cw",
    "1": "ccw"
}


class Decoder():
    """Decode on a message sending back from the pump."""

    def __init__(self, _resp_message=None):
        """Initialize the Decoder module."""
        self._last_msg = None  # Internal variable

        # Notify the upper layer a message has been received
        self._resp_message = _resp_message

    def set_last_message(self, last_msg: SentMessage):
        """Set the last message to sent to the pump."""
        self._last_msg = last_msg

    def get_last_message(self):
        """Safely retrieve the last sent message."""
        return self._last_msg

    def _update_message(self, recv_msg: ReceivedMessage):
        """Clear the last_msg that is waiting for response.

        Call the upper layer if the callback is set.
        """

        self._last_msg = None
        if self._resp_message:
            # Call the the callback function
            self._resp_message(recv_msg)

    def decode_status(self, recv_data: str):
        """Decode the status message from the pump.

        Args:
            - recv_data - data input str type

        Return:
            - json - decoded status message.
        """

        data = {"result": "invalid"}
        fields = recv_data.split(',')

        if len(fields) != 3:
            data["error"] = "Invalid data format"
            return data
        else:
            if int(fields[0]) < 1 or int(fields[0]) > 8:
                data["error"] = "Invalid serial address"
                return data

            motor_status = MOTOR_STATUS.get(fields[1])
            if motor_status is None:
                data["error"] = "Invalid motor status"
                return data

            direction = DIR.get(fields[2])
            if direction is None:
                data["error"] = "Invalid pump direction"
                return data

            return {
                "result": "data",
                "address": fields[0],
                "motor_status": motor_status,
                "direction": direction
            }

    def decode_speedp(self, recv_data: str):
        """Decode the speedp message from the pump.

        Args:
            - recv_data - data input str type

        Return:
            - json - decoded status message.
        """

        data = {"result": "Invalid"}

        try:
            speed = float(recv_data)
            result = int(speed)
            # Check the percentage value
            if result < 0.0 or result > 100.0:
                data["error"] = "Invalid percentage value"
                return data

            return {
                "result": "data",
                "speed": speed,
                "unit": "%"
            }
        except ValueError:
            data["error"] = "Invalid data format"
            return data

    def decode_volume(self, recv_data: str):
        """Decode the volume message from the pump.

        Args:
            - recv_data - data input str type

        Return:
            - json - decoded status message.
        """

        data = {"result": "Invalid"}

        try:
            numerical_value, unit = recv_data.split(' ')
            numerical_value = float(numerical_value)

            if unit.isnumeric():
                data["error"] = "Invalid data format"
                return data

            return {
                "result": "data",
                "volume": numerical_value,
                "unit": unit
            }
        except ValueError:
            data["error"] = "Invalid data format"
            return data

    def client_decode(self, str_data: str):
        """Decode the message sent from the pump.

        Args:
            - str_data - data input in ASCII string format

             It's assume that the pump sends one message at once
            A SET message will be responded with one character:
                * for valid set command
                # for invalid set command
                ~ for valid command but not in serial mode

            A GET message will be responded with actual value, the message
            format will be:
                {value} + ⓭ ❿

            Some messages can be both SET and GET i.g. SPEEDP or SPEEDR

        Returns:
            - output - there is no return for this message
            If the message is successfully decoded, and the callback
            is available. The _update_message()is called.
        """

        if isinstance(str_data, bytes):
            str_data = str_data.decode('utf-8', 'ignore')

        str_data = str_data.strip()

        if self.get_last_message() is None:
            # There is no message waiting for the response
            # Pump must send the message by itself
            raise Exception("Serial Communication - not expected any input")

        recv_msg = ReceivedMessage(self.get_last_message())

        if self.get_last_message().msg_type == SentMessageType.RESP_SET:
            # If it's SET command, the expected resp text is only 1 character
            if str_data == ReceivedMessageId.RESP_OK.value:
                recv_msg.success = True
                recv_msg.data["result"] = "OK"
            elif str_data == ReceivedMessageId.RESP_NO.value:
                recv_msg.data["result"] = "Invalid"
            elif str_data == ReceivedMessageId.RESP_NOT_IN_SERIAL_MODE.value:
                recv_msg.data["result"] = "Not in Serial Comms mode"
            else:
                recv_msg.data["result"] = "Not a pump message"

        else:
            # Expected response for GET command
            recv_msg.data["result"] = str_data

            if recv_msg.data['result'] == ReceivedMessageId.RESP_NOT_IN_SERIAL_MODE.value:
                recv_msg.data['result'] = "Not in Serial Comms mode"

            else:
                if recv_msg.sent_msg.id == SentMessageId.STATUS:
                    recv_msg.data = self.decode_status(str_data)

                elif recv_msg.sent_msg.id == SentMessageId.SPEEDR:
                    recv_msg.data = {"result": "data",
                                     "speed": float(str_data),
                                     "unit": "rpm"}

                elif recv_msg.sent_msg.id == SentMessageId.SPEEDP:
                    recv_msg.data = self.decode_speedp(str_data)

                elif recv_msg.sent_msg.id == SentMessageId.VOLUME:
                    recv_msg.data = self.decode_volume(str_data)

                elif recv_msg.sent_msg.id == SentMessageId.VOLUME_REV:
                    recv_msg.data = {"result": "data",
                                     "index": float(str_data),
                                     "unit": "rev"}

                elif recv_msg.sent_msg.id == SentMessageId.UNIT_INDEX:
                    recv_msg.data = {"result": "data",
                                     "index": int(str_data)}

                elif recv_msg.sent_msg.id == SentMessageId.ON_TIME_FULL:
                    recv_msg.data = {"result": "data",
                                     "on-time": str_data,
                                     "index": "HH:MM:SS.X"}

                elif recv_msg.sent_msg.id == SentMessageId.GET_SOFTWARE_VERSION:
                    recv_msg.data = {"result": "data",
                                     "version": str_data}

                elif recv_msg.sent_msg.id == SentMessageId.MODEL_AND_VERSION:
                    _model, _version = str_data.split(" ")
                    recv_msg.data = {"result": "data",
                                     "Model": _model,
                                     "SerialComm Version": int(_version)}

                elif recv_msg.sent_msg.id == SentMessageId.DISPENSE_STATUS:
                    _status = {
                        "+": "running",
                        "-": "stopped",
                    }
                    if _status is None:
                        return {"result": "error",
                                "message": "Invalid motor status"}
                    recv_msg.data = {"result": "data",
                                     "status": _status[str_data]}

                elif recv_msg.sent_msg.id == SentMessageId.OFF_TIME_FULL:
                    recv_msg.data = {"result": "data",
                                     "off-time": str_data,
                                     "unit": "HH:MM:SS.X"}

                elif recv_msg.sent_msg.id == SentMessageId.ON_TIME_DECISEC:
                    recv_msg.data = {"result": "data",
                                     "on-time": int(str_data),
                                     "unit": "1/10 sec"}

                elif recv_msg.sent_msg.id == SentMessageId.BATCH_COUNT:
                    _count, _total = str_data.split('/')
                    recv_msg.data = {"result": "data",
                                     "count": _count,
                                     "total": _total}

                else:
                    return {"result": "Invalid",
                            "error": "Pump data is not supported"}

        if self._update_message:
            self._update_message(recv_msg)


class SerialProtocol(asyncio.Protocol, Decoder):
    """Handle serial connection events and decode the message."""

    def __init__(self, _connection_made, _connection_lost, **kw):
        """Masterflex Serial asyncio protocol handler."""
        super(SerialProtocol, self).__init__(**kw)
        self._transport = None
        self.buffer = ""
        self.connection_made_callback = _connection_made
        self.connection_lost_callback = _connection_lost
        self._discard_task = None

    def connection_made(self, transport):
        """Notification that a connection is made with the serial transport."""
        self._transport = transport
        logger.info('IPC Serial Port opened: [%s]', transport)
        if self.connection_made_callback:
            self.connection_made_callback(self)

    def data_received(self, str_data):
        """Handle incoming serial data and ensures only full messages are processed correctly."""

        # Cancel timeout task since new data arrived
        if self._discard_task is not None:
            self._discard_task.cancel()

        str_data = str_data.decode('utf-8', 'ignore')  # Ensure decoding to string
        self.buffer += str_data  # Append new data to the buffer

        while "\r" in self.buffer or "\n" in self.buffer:  # Process only full messages
            for delimiter in ["\r", "\n"]:
                if delimiter in self.buffer:
                    message, self.buffer = self.buffer.split(delimiter, 1)  # Extract one complete message
                    full_message = message.strip()

                    # Allow processing of single-character responses like '*', '#', '~'
                    if len(full_message) > 0:
                        self.client_decode(full_message)

        # If buffer contains data but no newline, start a timeout before discarding it
        if len(self.buffer) > 0:
            self._discard_task = asyncio.create_task(self.discard_buffer())

    async def discard_buffer(self, timeout=2):
        """Clear the buffer if no new data arrives within a given time (default: 2 seconds)."""
        try:
            await asyncio.sleep(timeout)
            self.buffer = ""  # Clear buffer if no new data arrives
        except asyncio.CancelledError:
            # Task was cancelled because new data arrived
            return
        finally:
            if self._discard_task is asyncio.current_task():
                self._discard_task = None

    def connection_lost(self, exc):
        """Handle connection loss."""
        logger.info('MasterflexSerial port lost connection')
        if self.connection_lost_callback:
            self.connection_lost_callback()

    @property
    def transport(self):
        """Return the transport property."""
        return self._transport
