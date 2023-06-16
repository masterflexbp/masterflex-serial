"""Unit tests related to MasterflexSerial message module."""

import json
import pytest


from masterflexserial.message import SentMessage, SentMessageId, SentMessageType,\
    ReceivedMessage, ReceivedMessageId, create_message


@pytest.mark.parametrize(
    "id, msg_type, payload, addr, expected_result",
    [(SentMessageId.ENABLE, SentMessageType.RESP_SET, "1", "1", "1RE1\r"),
     (SentMessageId.ENABLE, SentMessageType.RESP_SET, "0", "1", "1RE0\r")]
)
def test_create_message(id, msg_type, payload, addr, expected_result):
    """Test create a message to send to Masterflex pump."""
    sent_msg = SentMessage(id, msg_type)
    assert create_message(sent_msg, payload, addr) == expected_result


@pytest.mark.parametrize(
    "msg_id, expected",
    [(SentMessageId.ENABLE, "RE"),
     (SentMessageId.START, "H"),
     (SentMessageId.STOP, "I"),
     (SentMessageId.DIR_CW, "J"),
     (SentMessageId.DIR_CCW, "K"),
     (SentMessageId.SPEEDR, "R"),
     (SentMessageId.UNIT_INDEX, "RA"),
     (SentMessageId.STATUS, "RC"),
     (SentMessageId.SPEEDP, "S"),
     (SentMessageId.SET_ADDR, "@"),
     (SentMessageId.VOLUME, ":"),
     (SentMessageId.VOLUME_REV, "RB")]
)
def test_sent_message_id(msg_id, expected):
    """Test sent message Id enum."""
    assert msg_id.value == expected


@pytest.mark.parametrize(
    "msg_type, expected",
    [(SentMessageType.RESP_GET, "get"),
     (SentMessageType.RESP_SET, "set")]
)
def test_sent_message_type(msg_type, expected):
    """Test sent message type enum."""
    assert msg_type.value == expected


@pytest.mark.parametrize(
    "recv_id, expected",
    [(ReceivedMessageId.RESP_OK, "*"),
     (ReceivedMessageId.RESP_NO, "#"),
     (ReceivedMessageId.RESP_NOT_IN_SERIAL_MODE, "~"),
     (ReceivedMessageId.RESP_DATA, "data")]
)
def test_received_message_id(recv_id, expected):
    """Test sent message type enum."""
    assert recv_id.value == expected


@pytest.mark.parametrize(
    "id, msg_type, name",
    [(SentMessageId.ENABLE, SentMessageType.RESP_SET, "enable"),
     (SentMessageId.ENABLE, SentMessageType.RESP_SET, "disable"),
     (SentMessageId.ENABLE, SentMessageType.RESP_SET, None)]
)
def test_sent_message(id, msg_type, name):
    """Test create a message to send to Masterflex pump."""
    sent_msg = SentMessage(id, msg_type, name)

    # Test the __str__() function to create the sent_msg object
    sent_msg_json = json.loads(str(sent_msg))

    assert sent_msg_json["id"] == id.value
    assert sent_msg_json["type"] == msg_type.value
    assert sent_msg_json["name"] == name


@pytest.mark.parametrize(
    "id, msg_type, name, data",
    [(SentMessageId.ENABLE, SentMessageType.RESP_SET, "enable", "{'result:', 'OK'}"),
     (SentMessageId.ENABLE, SentMessageType.RESP_SET, "disable", "{'result:', 'Invalid'}"),
     (SentMessageId.ENABLE, SentMessageType.RESP_SET, None, "{}")]
)
def test_received_message(id, msg_type, name, data):
    """Test create a message to send to Masterflex pump."""
    sent_msg = SentMessage(id, msg_type, name)
    recv_msg = ReceivedMessage(sent_msg, data)

    assert recv_msg.success is False

    # Test the __str__() function to create the recv_msg object
    recv_msg_json = json.loads(str(recv_msg))

    assert recv_msg_json["id"] == sent_msg.id.value
    assert recv_msg_json["name"] == name
    assert recv_msg_json["data"] == data
