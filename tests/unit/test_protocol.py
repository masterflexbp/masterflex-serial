"""Unit tests related to MasterflexSerial protocol."""

import asyncio
import pytest
from masterflexserial.message import SentMessage, SentMessageId, SentMessageType, \
    ReceivedMessage
from masterflexserial.protocol import Decoder, SerialProtocol
from unittest.mock import Mock, AsyncMock


class TestDecoder:
    """Unit tests for the Decode responded message from the pump."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "str_data, expected_buffer", [
            ("Complete data\r", ""),                 # Delimited message → processed
            ("Incomplete data", "Incomplete data"),  # No delimiter → stays in buffer
            ("", ""),                                # Empty input
        ])
    async def test_data_received(self, str_data, expected_buffer):
        """Test that data_received() correctly handles various buffer scenarios."""
        uut = SerialProtocol(None, None)

        # Mock decode behavior
        mock_data = Mock()
        mock_data.decode.return_value = str_data

        uut.client_decode = Mock()  # Mock client_decode to prevent real decoding logic
        uut.discard_buffer = AsyncMock()  # Mock discard_buffer to inspect call args

        # Call method
        uut.data_received(mock_data)

        # If discard_buffer should've been triggered
        if len(expected_buffer) > 0:
            uut.discard_buffer.assert_called_once()
            args = uut.discard_buffer.call_args.args

            # Accept either no arguments or an int
            assert len(args) == 0 or isinstance(args[0], int), (
                f"discard_buffer should be called with no arguments or an int, got: {args}"
            )

        # Final buffer check
        assert uut.buffer == expected_buffer

    def test_set_last_message(self):
        """Test set the last message."""
        # Given a protocol packet decoder
        uut = Decoder()
        sent_msg = SentMessage(SentMessageId.ENABLE, SentMessageType.RESP_SET, "enable")
        uut.set_last_message(sent_msg)
        assert uut._last_msg.id == sent_msg.id
        assert uut._last_msg.msg_type == sent_msg.msg_type
        assert uut._last_msg.name == sent_msg.name

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "initial_buffer, timeout, expected_buffer", [
            ("Incomplete data", 1, ""),  # Cleared buffer after timeout
            ("", 1, "")])  # Empty buffer should remain empty
    async def test_discard_buffer(self, initial_buffer, timeout, expected_buffer):
        """Test that discard_buffer() correctly handles various buffer scenarios."""

        uut = SerialProtocol(None, None)
        uut.buffer = initial_buffer
        uut._discard_task = asyncio.create_task(uut.discard_buffer(timeout=timeout))
        await uut._discard_task
        assert uut.buffer == expected_buffer, f"Expected buffer: '{expected_buffer}', but got: '{uut.buffer}'"
        assert not hasattr(uut, "_'discard_task"), "_discard_task was not deleted"

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
