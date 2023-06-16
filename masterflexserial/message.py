"""This module defines the sent and received messages, and create_message() function."""
import enum
import json
import logging

logger = logging.getLogger(__name__)


class SentMessageId(enum.Enum):
    """All supported Masterflex Serial Messages that the pump can accept.

    These messages are sent from client side to the pump

    A SET message will be responded with:
        * for valid set command
        # for invalid set command
        ~ for valid command but not in serial mode
    A GET message will be responded with actual value, the format:
        {value} + ⓭ ❿
    Some messages can be both SET and GET i.g. SPEEDP or SPEEDR
    """

    ENABLE = "RE"
    STATUS = "RC"
    START = "H"
    STOP = "I"
    DIR_CW = "J"
    DIR_CCW = "K"
    SPEEDR = "R"
    SPEEDP = "S"
    SET_ADDR = "@"
    VOLUME = ":"
    VOLUME_REV = "RB"
    UNIT_INDEX = "RA"
    RESET_CUMULATIVE = "W"


class SentMessageType(enum.Enum):
    """Respond messages from the Masterflex pump."""

    RESP_GET = "get"
    RESP_SET = "set"


class SentMessage:
    """Serial message to send to the pump and its type."""

    def __init__(self, id: SentMessageId, msg_type: SentMessageType, name: str = ""):
        """Create a serial message."""
        self.id = id
        self.msg_type = msg_type
        # Additional name to differentiate the message with the same ID
        # like enable and disable
        self.name = name

    def __str__(self):
        """Implement string function."""
        msg = {
            "id": self.id.value,
            "type": self.msg_type.value,
            "name": self.name,
        }
        return json.dumps(msg)


class ReceivedMessageId(enum.Enum):
    """These message IDs are sent back from the pump.

    A SET message will be responded with:
        * for valid set command
        # for invalid set command
        ~ for valid command but not in serial mode
    A GET message will be responded with actual value, the format:
        {value} + ⓭ ❿
    Some messages can be both SET and GET i.g. SPEEDP or SPEEDR.
    """

    RESP_OK = "*"
    RESP_NO = "#"
    RESP_NOT_IN_SERIAL_MODE = "~"
    RESP_DATA = "data"


class ReceivedMessage:
    """Format of a received message from the pump."""

    def __init__(self, sent_msg: SentMessage, data: json = None):
        """Create a message that is sent back from the pump."""

        self.success = False
        self.sent_msg = sent_msg
        self.data = data
        if data is None:
            self.data = {}

    def __str__(self):
        """Implement string function."""
        msg = {
            "success": self.success,
            "id": self.sent_msg.id.value,
            "name": self.sent_msg.name,
            "data": self.data
        }
        return json.dumps(msg)


def xstr(text: str):
    """Return empty string if None."""
    if text is None:
        return ""
    else:
        return text


def create_message(msg: SentMessage, payload: str, addr: str = '1'):
    """Create a serial message to send to the pump.

    msg: message to send to the pump
    payload: message payload
    addr: address of the pump - default 1
    """
    if msg.id == SentMessageId.SET_ADDR:
        return str(SentMessageId.SET_ADDR.value) + str(payload) + chr(13)

    return str(addr) + str(msg.id.value) + xstr(payload) + chr(13)
