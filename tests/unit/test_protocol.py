"""Unit tests related to MasterflexSerial protocol."""

import pytest
from masterflexserial.message import SentMessage, SentMessageId, SentMessageType,\
    ReceivedMessage
from masterflexserial.protocol import Decoder


class TestDecoder:
    """Unit tests for the Decode responded message from the pump."""

    def test_set_last_message(self):
        """Test set the last message."""
        # Given a protocol packet decoder
        uut = Decoder()
        sent_msg = SentMessage(SentMessageId.ENABLE, SentMessageType.RESP_SET, "enable")
        uut.set_last_message(sent_msg)
        assert uut.last_msg.id == sent_msg.id
        assert uut.last_msg.msg_type == sent_msg.msg_type
        assert uut.last_msg.name == sent_msg.name

    @pytest.mark.parametrize(
        "message_text, expected", [
            ("*", "OK"),
            ("#", "Invalid"),
            ("~", "Not in Serial Comms mode")]
    )
    def test_client_decode(self, message_text, expected):
        """Verify that responded messages from pump is decoded correctly."""

        self.recv_msg: ReceivedMessage = None

        def recv_message_callback(msg: ReceivedMessage):
            self.recv_msg = msg

        uut = Decoder(recv_message_callback)
        sent_msg = SentMessage(SentMessageId.ENABLE, SentMessageType.RESP_SET, "enable")
        uut.set_last_message(sent_msg)
        uut.client_decode(message_text.encode('utf-8'))
        assert self.recv_msg.data["result"] == expected
        assert self.recv_msg.sent_msg.id == sent_msg.id

    @pytest.mark.parametrize(
        "input, expected",
        [("1,0,0", {'result': 'data', 'address': '1', 'motor_status': 'stopped', 'direction': 'cw'}),
         ("1,0,1", {'result': 'data', 'address': '1', 'motor_status': 'stopped', 'direction': 'ccw'}),
         ("1,1,0", {'result': 'data', 'address': '1', 'motor_status': 'running', 'direction': 'cw'}),
         ("1,1,1", {'result': 'data', 'address': '1', 'motor_status': 'running', 'direction': 'ccw'}),
         ("9,0,0", {'result': 'invalid', 'error': 'Invalid serial address'}),
         ("1,2,0", {'result': 'invalid', 'error': 'Invalid motor status'}),
         ("1,0,2", {'result': 'invalid', 'error': 'Invalid pump direction'})]
    )
    @pytest.mark.asyncio
    async def test_decode_status(self, input, expected):
        """Verify that reponded status message from pump is decoded correctly."""

        uut = Decoder()
        sent_msg = SentMessage(SentMessageId.STATUS, SentMessageType.RESP_GET, "status")
        recv_msg = ReceivedMessage(sent_msg)
        output = uut.decode_status(input)
        for k in output.keys():
            assert output[k] == expected[k]
        assert recv_msg.sent_msg.id == sent_msg.id

    @pytest.mark.parametrize(
        "input, expected",
        [("60.0", {'result': 'data', 'speed': 60.0, 'unit': '%'}),
         ("", {'result': 'Invalid', 'error': 'Invalid data format'}),
         ("6x", {'result': 'Invalid', 'error': 'Invalid data format'}),
         ("6 0", {'result': 'Invalid', 'error': 'Invalid data format'}),
         ("-1", {'result': 'Invalid', 'error': 'Invalid percentage value'}),
         ("101", {'result': 'Invalid', 'error': 'Invalid percentage value'})]
    )
    @pytest.mark.asyncio
    async def test_decode_speedp(self, input, expected):
        """Verify that reponded status message from pump is decoded correctly."""

        uut = Decoder()
        sent_msg = SentMessage(SentMessageId.SPEEDP, SentMessageType.RESP_GET, "speedp")
        recv_msg = ReceivedMessage(sent_msg)
        output = uut.decode_speedp(input)
        for k in output.keys():
            assert output[k] == expected[k]
        assert recv_msg.sent_msg.id == sent_msg.id

    @pytest.mark.parametrize(
        "input, expected",
        [("20993.466 mL", {'result': 'data', 'volume': 20993.466, 'unit': 'mL'}),
         ("x mL", {'result': 'Invalid', 'error': 'Invalid data format'}),
         ("", {'result': 'Invalid', 'error': 'Invalid data format'}),
         ("20993.466 0", {'result': 'Invalid', 'error': 'Invalid data format'})]
    )
    @pytest.mark.asyncio
    async def test_decode_volume(self, input, expected):
        """Verify that reponded status message from pump is decoded correctly."""

        uut = Decoder()
        sent_msg = SentMessage(SentMessageId.VOLUME, SentMessageType.RESP_GET, "volume")
        recv_msg = ReceivedMessage(sent_msg)
        output = uut.decode_volume(input)
        for k in output.keys():
            assert output[k] == expected[k]
        assert recv_msg.sent_msg.id == sent_msg.id
