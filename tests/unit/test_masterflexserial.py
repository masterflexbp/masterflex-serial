"""Unit tests related to MasterflexSerial main module."""
import json
import asyncio
from unittest.mock import MagicMock, patch

import pytest
import serial_asyncio

from masterflexserial.masterflexserial import MasterflexSerial
from masterflexserial.message import SentMessage, SentMessageId, SentMessageType, ReceivedMessage


@pytest.mark.asyncio
async def test_serial_connection():
    """Verify that the serial client requests to create a serial connection."""
    serial_transport = MagicMock()
    serial_protocol = MagicMock()

    async def mock_create_serial_connection(*args, **kwargs):
        return (serial_transport, serial_protocol)

    with patch.object(
        serial_asyncio,
        'create_serial_connection',
        side_effect=mock_create_serial_connection
    ) as mock_create:
        mflx = MasterflexSerial("/dev/pts/1234", 115200)
        await mflx.connect()
        assert mock_create.called


@pytest.mark.asyncio
async def test_addr():
    """Verify that the serial address is set correctly by default."""
    mflx = MasterflexSerial("/dev/pts/1234")
    assert mflx.addr == "1"


@pytest.mark.asyncio
async def test_baud_rate():
    """Verify that the serial address is set correctly by default."""
    mflx = MasterflexSerial("/dev/pts/1234")
    assert mflx.baud_rate == 115200
    assert mflx.port == "/dev/pts/1234"


@pytest.fixture
def mflx_serial():
    """Masterflex Serial Pytest fixture."""
    mflx = MasterflexSerial("/dev/pts/1234")
    mflx._protocol = MagicMock()
    mflx._protocol.transport = MagicMock()
    return mflx


async def mock_recv_data(mflx: MasterflexSerial, sent_msg: SentMessage, expected: json):
    """Mock the data return from the serial port."""
    await asyncio.sleep(0.1)
    mflx._received_response_message(ReceivedMessage(sent_msg, expected))


@pytest.mark.parametrize(
    "msg_id, expected_result",
    [(SentMessageId.ENABLE, {"result": "OK"}),
     (SentMessageId.ENABLE, {"result": "Invalid"}),
     (SentMessageId.ENABLE, {"result": "Not a pump message"})]
)
@pytest.mark.asyncio
async def test_enable(mflx_serial: MasterflexSerial, msg_id: SentMessageId, expected_result: json):
    """Verify that the ENABLE message is sent and received correctly to the pump."""

    sent_msg = SentMessage(msg_id, SentMessageType.RESP_SET)
    enable_task = asyncio.create_task(mflx_serial.enable())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    try:
        await asyncio.gather(enable_task, recv_data_task)
    finally:
        data = enable_task.result()
        for k, val in data.items():
            assert val == expected_result[k]


@pytest.mark.parametrize(
    "msg_id, expected_result",
    [(SentMessageId.ENABLE, {"result": "OK"}),
     (SentMessageId.ENABLE, {"result": "Invalid"}),
     (SentMessageId.ENABLE, {"result": "Not a pump message"})]
)
@pytest.mark.asyncio
async def test_disable(mflx_serial: MasterflexSerial, msg_id: SentMessageId, expected_result: json):
    """Verify that the DISABLE message is sent correctly to the pump."""

    sent_msg = SentMessage(msg_id, SentMessageType.RESP_SET)
    disable_task = asyncio.create_task(mflx_serial.disable())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    try:
        await asyncio.gather(disable_task, recv_data_task)
    finally:
        data = disable_task.result()
        for k, val in data.items():
            assert val == expected_result[k]


@pytest.mark.parametrize(
    "expected_result",
    [({'result': 'data', 'address': '1', 'motor_status': 'stopped', 'direction': 'cw'}),
     ({'result': 'data', 'address': '1', 'motor_status': 'running', 'direction': 'ccw'}),
     ({'result': 'data', 'address': '1', 'motor_status': 'stopped', 'direction': 'cw'}),
     ({'result': 'data', 'address': '1', 'motor_status': 'running', 'direction': 'ccw'}),
     ({'result': 'invalid', 'error': 'Invalid serial address'}),
     ({'result': 'invalid', 'error': 'Invalid motor status'}),
     ({'result': 'invalid', 'error': 'Invalid pump direction'})]
)
@pytest.mark.asyncio
async def test_status(mflx_serial: MasterflexSerial, expected_result: json):
    """Verify that the STATUS message is sent correctly to the pump.

    Plus, verify that the received message is handled correctly.
    """

    sent_msg = SentMessage(SentMessageId.STATUS, SentMessageType.RESP_GET, "status")
    get_status_task = asyncio.create_task(mflx_serial.status())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    # Call the status() function and await the response
    try:
        await asyncio.gather(get_status_task, recv_data_task)
    finally:
        data = get_status_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "expected_result",
    [({"result": "OK"}),
     ({"result": "Invalid"}),
     ({"result": "*$()&"}),
     ({"result": "Not in Serial Comms mode"})]
)
@pytest.mark.asyncio
async def test_start(mflx_serial: MasterflexSerial, expected_result: json):
    """Verify that the START message is sent correctly to the pump."""

    sent_msg = SentMessage(SentMessageId.START, SentMessageType.RESP_SET)
    start_task = asyncio.create_task(mflx_serial.start())

    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    try:
        await asyncio.gather(start_task, recv_data_task)
    finally:
        data = start_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "expected_result",
    [({"result": "OK"}),
     ({"result": "Invalid"}),
     ({"result": "*$()&"}),
     ({"result": "Not in Serial Comms mode"})]
)
@pytest.mark.asyncio
async def test_stop(mflx_serial, expected_result: json):
    """Verify that the STOP SET message is sent correctly to the pump."""

    sent_msg = SentMessage(SentMessageId.STOP, SentMessageType.RESP_SET)
    stop_task = asyncio.create_task(mflx_serial.stop())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    try:
        await asyncio.gather(stop_task, recv_data_task)
    finally:
        data = stop_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "input, expected_result",
    [("50", {"result": "OK"}),
     ("00605", {"result": "Invalid", "error": "Speed in percent must be from 0 to 100"}),
     ("-9", {"result": "Invalid", "error": "Speed in percent must be from 0 to 100"}),
     ("101", {"result": "Invalid", "error": "Speed in percent must be from 0 to 100"}),
     ("50", {"result": "Not in Serial Comms mode"}),
     ("abc", {"result": "Invalid", "error": "Not a number. Speed in percent must be from 0 to 100"})]
)
@pytest.mark.asyncio
async def test_speedp_set(mflx_serial, input, expected_result):
    """Verify that the SPEEDP set message is sent correctly to the pump.

    Plus, verify that the received message is handled correctly.
    """

    sent_msg = SentMessage(SentMessageId.SPEEDP, SentMessageType.RESP_SET, "speedp")
    set_speedp_task = asyncio.create_task(mflx_serial.speed_percent(input))
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    # Call the SET speed_percent() function and await the response
    try:
        await asyncio.gather(set_speedp_task, recv_data_task)
    finally:
        data = set_speedp_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "expected_result",
    [({'result': 'data', 'speed': '60.0', 'unit': '%'}),
     ({'result': 'invalid', 'error': 'Invalid data format'}),
     ({'result': 'invalid', 'error': 'Invalid percentage value'})]
)
@pytest.mark.asyncio
async def test_speedp_get(mflx_serial, expected_result):
    """Verify that the SPEEDP get message is recieve correctly from the pump.

    Plus, verify that the received message is handled correctly.
    """

    sent_msg = SentMessage(SentMessageId.SPEEDP, SentMessageType.RESP_GET, "speedp")
    get_speedp_task = asyncio.create_task(mflx_serial.speed_percent())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    # Call the GET speed_percent() function and await the response
    try:
        await asyncio.gather(get_speedp_task, recv_data_task)
    finally:
        data = get_speedp_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "msg_id, name, dir, expected_result",
    [(SentMessageId.DIR_CW, "dir_cw", "cw", {"result": "OK"}),
     (SentMessageId.DIR_CW, "dir_cw", "cw", {"result": "Not in Serial Comms mode"}),
     (SentMessageId.DIR_CCW, "dir_ccw", "ccw", {"result": "OK"}),
     (SentMessageId.DIR_CCW, "dir_ccw", "ccw", {"result": "Not in Serial Comms mode"}),
     (None, "invalid", "c-cw", {"result": "Invalid", "error": "Invalid param. Valid inputs: 'cw' or 'ccw'"})]
)
@pytest.mark.asyncio
async def test_dir(mflx_serial, msg_id, name, dir, expected_result):
    """Verify that the DIRECTION SET message is sent correctly to the pump."""

    sent_msg = SentMessage(msg_id, SentMessageType.RESP_SET, name)
    dir_task = asyncio.create_task(mflx_serial.set_dir(dir))
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    try:
        await asyncio.gather(dir_task, recv_data_task)
    finally:
        data = dir_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "resp_type, name, value, expected_result",
    [(SentMessageType.RESP_GET, "get_speedr", None, {'result': 'data', 'speed': '105.00', 'unit': 'RPM'}),
     (SentMessageType.RESP_GET, "get_speedr", None, {"result": "Not in Serial Comms mode"}),
     (SentMessageType.RESP_SET, "set_speedr", "205.75", {"result": "OK"}),
     (SentMessageType.RESP_SET, "set_speedr", "150", {"result": "OK"}),
     (SentMessageType.RESP_SET, "set_speedr", "175.4579249", {"result": "OK"}),
     (SentMessageType.RESP_SET, "set_speedr", "800", {"result": "Invalid"}),
     (SentMessageType.RESP_SET, "set_speedr", "175.45", {"result": "Not in Serial Comms mode"}),
     (SentMessageType.RESP_SET, "set_speedr", "abc", {"result": "Invalid",
      "error": "Invalid param. Valid inputs: int or float"}),
     (SentMessageType.RESP_SET, "set_speedr", "99999", {"result": "Invalid",
      "error": "Value out of range. Pumps range in RPM: 0 to 9999.99"})]
)
@pytest.mark.asyncio
async def test_speed_rpm(mflx_serial, resp_type, name, value, expected_result):
    """Verify that the GET/SET speed in RPM message is sent correctly to/from the pump."""

    sent_msg = SentMessage(SentMessageId.SPEEDR, resp_type, name)
    speed_rpm_task = asyncio.create_task(mflx_serial.speed_rpm(value))
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    try:
        await asyncio.gather(speed_rpm_task, recv_data_task)
    finally:
        data = speed_rpm_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "input, expected_result",
    [("1", {"result": "OK"}),
     ("9", {"result": "Invalid", "error": "Address must be between 1 and 8"}),
     ("1.2", {"result": "Invalid", "error": "Not a valid number. Address must be integer between 1 and 8"}),
     ("abc", {"result": "Invalid", "error": "Not a valid number. Address must be integer between 1 and 8"})]
)
@pytest.mark.asyncio
async def test_addr_set(mflx_serial, input, expected_result):
    """Verify that the ADDR SET message is sent correctly to the pump.

    Plus, verify that the received message is handled correctly.
    """

    sent_msg = SentMessage(SentMessageId.SET_ADDR, SentMessageType.RESP_SET, "id")
    set_addr_task = asyncio.create_task(mflx_serial.set_addr(input))
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    # Call the set_addr() function and await the response
    try:
        await asyncio.gather(set_addr_task, recv_data_task)
    finally:
        data = set_addr_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "expected_result",
    [({'result': 'data', 'volume': 20993.466, 'unit': 'mL'}),
     ({'result': 'Not in Serial Comms mode'})]
)
@pytest.mark.asyncio
async def test_volume_get(mflx_serial, expected_result):
    """Verify that the VOLUME get message is recieve correctly from the pump.

    Plus, verify that the received message is handled correctly.
    """

    sent_msg = SentMessage(SentMessageId.VOLUME, SentMessageType.RESP_GET, "volume")
    get_volume_task = asyncio.create_task(mflx_serial.volume())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    # Call the volume() function and await the response
    try:
        await asyncio.gather(get_volume_task, recv_data_task)
    finally:
        data = get_volume_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "expected_result",
    [({'result': 'data', 'volume': 7497.667, 'unit': 'rev'}),
     ({'result': 'Not in Serial Comms mode'})]
)
@pytest.mark.asyncio
async def test_volume_rev_get(mflx_serial, expected_result):
    """Verify that the VOLUME get message is recieve correctly from the pump.

    Plus, verify that the received message is handled correctly.
    """

    sent_msg = SentMessage(SentMessageId.VOLUME_REV, SentMessageType.RESP_GET, "volume_rev")
    get_volume_rev_task = asyncio.create_task(mflx_serial.volume_rev())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    # Call the volume_rev() function and await the response
    try:
        await asyncio.gather(get_volume_rev_task, recv_data_task)
    finally:
        data = get_volume_rev_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "expected_result",
    [({"result": "OK"}),
     ({"result": "Invalid"}),
     ({"result": "*$()&"}),
     ({"result": "Not in Serial Comms mode"})]
)
@pytest.mark.asyncio
async def test_reset_cumulative(mflx_serial, expected_result):
    """Verify that the RESET Cumulative Volume message is sent correctly to the pump."""

    sent_msg = SentMessage(SentMessageId.RESET_CUMULATIVE, SentMessageType.RESP_SET)
    reset_cumulative_task = asyncio.create_task(mflx_serial.reset_cumulative())
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    # Call the reset_cumulative() function and await the response
    try:
        await asyncio.gather(reset_cumulative_task, recv_data_task)
    finally:
        data = reset_cumulative_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "resp_type, name, value, expected_result",
    [(SentMessageType.RESP_GET, "get_index", None, {'result': 'data', 'index': '3'}),
     (SentMessageType.RESP_GET, "get_index", None, {"result": "Not in Serial Comms mode"}),
     (SentMessageType.RESP_SET, "set_index", "03", {"result": "OK"}),
     (SentMessageType.RESP_SET, "set_index", "07", {"result": "Not in Serial Comms mode"}),
     (SentMessageType.RESP_SET, "set_index", "5", {"result": "OK"}),
     (SentMessageType.RESP_SET, "set_index", "000001", {"result": "OK"}),
     (SentMessageType.RESP_SET, "set_index", "abc", {"result": "Invalid",
      "error": "Invalid param. Valid inputs: integer"}),
     (SentMessageType.RESP_SET, "set_index", "35", {"result": "Invalid",
      "error": "Value out of range. Pumps flow unit index range: 0 to 32"})]
)
@pytest.mark.asyncio
async def test_unit_index(mflx_serial, resp_type, name, value, expected_result):
    """Verify that the GET/SET flow unit index is sent correctly to/from the pump."""

    sent_msg = SentMessage(SentMessageId.UNIT_INDEX, resp_type, name)
    unit_index_task = asyncio.create_task(mflx_serial.unit_index(value))
    recv_data_task = asyncio.create_task(mock_recv_data(mflx_serial, sent_msg, expected_result))

    try:
        await asyncio.gather(unit_index_task, recv_data_task)
    finally:
        data = unit_index_task.result()
        for k, v in data.items():
            assert v == expected_result[k]


@pytest.mark.parametrize(
    "time, expected_result, expected_payload",
    [
        # Case 1: GET request
        (None, {"result": "data", "on-time": "00:00:10.0", "unit": "HH:MM:SS.X"}, None),

        # Case 2: Valid inputs within range
        ("00:00:00.1", {"result": "OK"}, "0000001"),
        ("01:02:03.4", {"result": "OK"}, "0102034"),
        ("99:59:59.9", {"result": "OK"}, "9959599"),

        # Case 3: Invalid format
        ("invalid", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("-01:02:03.4", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("12:1:15.2", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("123:45:67.8", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),

        # Case 4: Out of range
        ("00:00:00.0", {"result": "Invalid", "error": "Time not within the range"}, None),
        ("100:00:00.0", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("99:60:59.9", {"result": "Invalid", "error": "Time not within the range"}, None),
    ]
)
@pytest.mark.asyncio
async def test_on_time_full(mflx_serial, time, expected_result, expected_payload):
    """Test the on_time_full method with various arguments."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        if time is None:  # Simulated GET response
            return {"result": "data", "on-time": "00:00:10.0", "unit": "HH:MM:SS.X"}
        return {"result": "OK"}  # Simulated SET response

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    result = await mflx_serial.on_time_full(time)

    # Validate the result
    assert result == expected_result

    # Validate the payload for SET requests
    if time is None:  # GET case
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, addr = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.ON_TIME_FULL
        assert sent_message.msg_type == SentMessageType.RESP_GET
        assert payload is None
    elif isinstance(expected_payload, str):  # Valid SET case
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, addr = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.ON_TIME_FULL
        assert sent_message.msg_type == SentMessageType.RESP_SET
        assert payload == expected_payload
    else:  # Invalid input
        mflx_serial._send_message.assert_not_called()


@pytest.mark.parametrize(
    "enable, expected_message_id",
    [
        (True, SentMessageId.SET_PANEL_ACTIVE),
        (False, SentMessageId.SET_PANEL_INACTIVE),
        ("abc", None),
    ]
)
@pytest.mark.asyncio
async def test_set_panel_active(mflx_serial, enable, expected_message_id):
    """Test that the correct serial message is sent."""

    async def mock_send_message(sent_message, *args, **kwargs):
        return sent_message.id.value  # Simulate returning the SentMessageId

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)
    task = asyncio.create_task(mflx_serial.set_panel_active(enable))
    done, _ = await asyncio.wait([task])
    result = list(done)[0].result()

    if isinstance(enable, bool):
        assert result == expected_message_id.value
    else:
        mflx_serial._send_message.assert_not_called()
        assert result == {"result": "Invalid", "error": "Invalid param. Valid inputs: True or False"}


@pytest.mark.parametrize(
    "mode, expected_message_id, expected_result",
    [
        ("continuous", SentMessageId.SET_DISPENSE_CONTINUOUS, {"result": "OK"}),
        ("time", SentMessageId.SET_DISPENSE_TIME, {"result": "OK"}),
        ("invalid_mode", None, {"result": "Invalid", "error": "Invalid param. Valid inputs: 'continuous' or 'time'"}),
    ]
)
@pytest.mark.asyncio
async def test_set_dispense_mode(mflx_serial, mode, expected_message_id, expected_result):
    """Test for setting the pump's dispense mode."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, *args, **kwargs):
        return {"result": "OK"}

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    task = asyncio.create_task(mflx_serial.set_dispense_mode(mode))
    done, _ = await asyncio.wait([task])
    result = list(done)[0].result()
    assert result == expected_result

    # Validate behavior based on expected_message_id
    if expected_message_id:  # For valid inputs
        assert mflx_serial._send_message.call_count == 1
        sent_message, *_ = mflx_serial._send_message.call_args[0]
        assert sent_message.id == expected_message_id
        assert sent_message.msg_type == SentMessageType.RESP_SET
    else:  # For invalid inputs
        mflx_serial._send_message.assert_not_called()


@pytest.mark.parametrize(
    "serial_mode, expected_response",
    [
        (True, {"result": "OK", "version": "1.2.3"}),  # Pump is in serial mode
        (False, {"result": "Error", "error": "Pump not in Serial Comms mode"}),  # Pump not in serial mode
    ]
)
@pytest.mark.asyncio
async def test_get_software_version(mflx_serial, serial_mode, expected_response):
    """Test for getting the software version of the pump."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, *args, **kwargs):
        if serial_mode:
            return {"result": "OK", "version": "1.2.3"}
        else:
            return {"result": "Error", "error": "Pump not in Serial Comms mode"}

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    result = await mflx_serial.get_software_version()
    assert mflx_serial._send_message.call_count == 1
    sent_message, *_ = mflx_serial._send_message.call_args[0]
    assert sent_message.id == SentMessageId.GET_SOFTWARE_VERSION
    assert sent_message.msg_type == SentMessageType.RESP_GET
    assert result == expected_response


@pytest.mark.parametrize(
    "time, expected_result, expected_payload",
    [
        ("100", {"result": "OK"}, "100"),
        ("500", {"result": "OK"}, "500"),
        (0, {"result": "Invalid", "error": "Value out of range. Pumps flow unit index range: 1 to 999"}, None),
        (1, {"result": "OK"}, "001"),
        (999, {"result": "OK"}, "999"),
        (1000, {"result": "Invalid", "error": "Value out of range. Pumps flow unit index range: 1 to 999"}, None),
        ("invalid", {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}, None),
        (5.5, {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}, None),
    ]
)
@pytest.mark.asyncio
async def test_on_time_minutes(mflx_serial, time, expected_result, expected_payload):
    """Test the on_time method with various arguments."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        return {"result": "OK"}  # Simulated SET response
    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    result = await mflx_serial.on_time_min(time)
    assert result == expected_result

    if expected_payload is not None:
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, _ = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.SET_ON_TIME_MIN
        assert sent_message.msg_type == SentMessageType.RESP_SET
        assert payload == expected_payload
    else:
        mflx_serial._send_message.assert_not_called()


@pytest.mark.parametrize(
    "time, expected_result, expected_payload",
    [
        ("6", {"result": "OK"}, "06"),
        ("50", {"result": "OK"}, "50"),
        (0, {"result": "Invalid", "error": "Value out of range. On Time hour range: 1 to 99"}, None),
        (1, {"result": "OK"}, "01"),
        (99, {"result": "OK"}, "99"),
        (100, {"result": "Invalid", "error": "Value out of range. On Time hour range: 1 to 99"}, None),
        ("invalid", {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}, None),
        (5.5, {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}, None),
    ]
)
@pytest.mark.asyncio
async def test_on_time_hr(mflx_serial, time, expected_result, expected_payload):
    """Test the on_time_hr method with various arguments."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        return {"result": "OK"}  # Simulated SET response
    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    result = await mflx_serial.on_time_hr(time)
    assert result == expected_result

    if expected_payload is not None:
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, _ = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.SET_ON_TIME_HR
        assert sent_message.msg_type == SentMessageType.RESP_SET
        assert payload == expected_payload
    else:
        mflx_serial._send_message.assert_not_called()


@pytest.mark.parametrize(
    "mock_return",
    [
        {"result": "data", "Model": "PumpX", "SerialComm Version": 220},  # Valid response with data
    ]
)
@pytest.mark.asyncio
async def test_get_version__model(mflx_serial, mock_return):
    """Test the get_version__model command."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        return mock_return

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the get_version__model method
    await mflx_serial.get_version__model()

    # Assertions
    mflx_serial._send_message.assert_called_once()
    sent_message, payload, _ = mflx_serial._send_message.call_args[0]
    assert sent_message.id == SentMessageId.MODEL_AND_VERSION
    assert sent_message.msg_type == SentMessageType.RESP_GET
    assert payload is None


@pytest.mark.asyncio
async def test_store_configs(mflx_serial):
    """Test the store_configs method."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, *args, **kwargs):
        return True  # Simulate a successful response

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    await mflx_serial.store_configs()

    # Validate the result
    mflx_serial._send_message.assert_called_once()
    sent_message, payload, addr = mflx_serial._send_message.call_args[0]
    assert sent_message.id == SentMessageId.STORE_CONFIGS
    assert sent_message.msg_type == SentMessageType.RESP_SET
    assert payload is None


@pytest.mark.asyncio
async def test_restore_configs(mflx_serial):
    """Test the restore_configs method."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, *args, **kwargs):
        return True  # Simulate successful restore

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    await mflx_serial.restore_configs()

    # Validate the result
    mflx_serial._send_message.assert_called_once()
    sent_message, payload, addr = mflx_serial._send_message.call_args[0]
    assert sent_message.id == SentMessageId.RESTORE_CONFIGS
    assert sent_message.msg_type == SentMessageType.RESP_SET
    assert payload is None


@pytest.mark.parametrize(
    "mock_return",
    [
        {"result": "OK"},  # Valid response
        {"result": "Invalid"},  # Invalid response
        {"result": "Not in Serial Comms mode"},  # Not in Serial Comms mode
    ]
)
@pytest.mark.asyncio
async def test_reset_batch(mflx_serial, mock_return):
    """Test the reset_batch command."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        return mock_return

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)
    await mflx_serial.reset_batch()

    # Assertions
    mflx_serial._send_message.assert_called_once()
    sent_message, payload, _ = mflx_serial._send_message.call_args[0]
    assert sent_message.id == SentMessageId.RESET_BATCH_COUNT
    assert sent_message.msg_type == SentMessageType.RESP_SET
    assert payload is None


@pytest.mark.asyncio
async def test_dispense_status(mflx_serial):
    """Test the dispense_status command."""
    async def mock_send_message(sent_message, payload, addr):
        return {"Mock Obj"}

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the dispense_status method
    await mflx_serial.dispense_status()

    # Assertions
    mflx_serial._send_message.assert_called_once()
    sent_message, payload, _ = mflx_serial._send_message.call_args[0]
    assert sent_message.id == SentMessageId.DISPENSE_STATUS
    assert sent_message.msg_type == SentMessageType.RESP_GET
    assert payload is None


@pytest.mark.parametrize(
    "time, expected_result, expected_payload",
    [
        (None, {"result": "data", "off-time": "00:00:10.0", "unit": "HH:MM:SS.X"}, None),
        ("00:00:00.1", {"result": "OK"}, "0000001"),
        ("01:02:03.4", {"result": "OK"}, "0102034"),
        ("99:59:59.9", {"result": "OK"}, "9959599"),
        ("invalid", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("12:1:15.2", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("123:45:67.8", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("00:00:00.0", {"result": "Invalid", "error": "Time not within the range"}, None),
        ("100:00:00.0", {"result": "Invalid", "error": "Invalid time format. Expected format: HH:MM:SS.X"}, None),
        ("99:60:59.9", {"result": "Invalid", "error": "Time not within the range"}, None),
    ]
)
@pytest.mark.asyncio
async def test_off_time_full(mflx_serial, time, expected_result, expected_payload):
    """Test the off_time_full method with various arguments."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        if time is None:  # Simulated GET response
            return {"result": "data", "off-time": "00:00:10.0", "unit": "HH:MM:SS.X"}
        return {"result": "OK"}  # Simulated SET response

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    result = await mflx_serial.off_time_full(time)
    assert result == expected_result

    if time is None:  # GET case
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, addr = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.OFF_TIME_FULL
        assert sent_message.msg_type == SentMessageType.RESP_GET
        assert payload is None
    elif isinstance(expected_payload, str):  # Valid SET case
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, addr = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.OFF_TIME_FULL
        assert sent_message.msg_type == SentMessageType.RESP_SET
        assert payload == expected_payload
    else:  # Invalid input
        mflx_serial._send_message.assert_not_called()


@pytest.mark.parametrize(
    "time, expected_result, expected_payload",
    [
        (None, {"result": "data", "on-time": 120, "unit": "1/10 sec"}, None),
        (1, {"result": "OK"}, "0001"),
        ("100", {"result": "OK"}, "0100"),
        ("9999", {"result": "OK"}, "9999"),
        (100, {"result": "OK"}, "0100"),
        (9999, {"result": "OK"}, "9999"),
        (0, {"result": "Invalid", "error": "Value out of range. Pumps on time deciseconds range: 0 to 9999"}, None),
        (10000,
         {"result": "Invalid", "error": "Value out of range. Pumps on time deciseconds range: 0 to 9999"}, None),
        ("invalid", {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}, None),
        (5.5, {"result": "Invalid", "error": "Invalid param. Valid inputs: integer"}, None),
    ]
)
@pytest.mark.asyncio
async def test_on_time(mflx_serial, time, expected_result, expected_payload):
    """Test the on_time_decisecond method with various arguments."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        if sent_message.id == SentMessageId.ON_TIME_DECISEC and payload is None:
            return {"result": "data", "on-time": 120, "unit": "1/10 sec"}  # Simulated GET response
        return {"result": "OK"}  # Simulated SET response

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    result = await mflx_serial.on_time_decisecond(time)
    assert result == expected_result

    if time is None:  # Case 1: GET on-time
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, _ = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.ON_TIME_DECISEC
        assert sent_message.msg_type == SentMessageType.RESP_GET
        assert payload == expected_payload
    elif expected_payload is not None:  # Case 2: Valid SET on-time
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, _ = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.ON_TIME_DECISEC
        assert sent_message.msg_type == SentMessageType.RESP_SET
        assert payload == expected_payload
    else:  # Case 3: Invalid input
        mflx_serial._send_message.assert_not_called()


@pytest.mark.parametrize(
    "batch_count, expected_result, expected_payload",
    [
        (None, {"result": "data", "count": 10, "total": 100}, None),
        (-1, {"result": "Invalid", "error": "Value must be between 0 and 99999"}, None),
        (0, {"result": "OK"}, "00000"),
        (12345, {"result": "OK"}, "12345"),
        (99999, {"result": "OK"}, "99999"),
        (100000, {"result": "Invalid", "error": "Value must be between 0 and 99999"}, None),
        ("invalid", {"result": "Invalid", "error": "Not an integer"}, None),
        (5.5, {"result": "Invalid", "error": "Not an integer"}, None),
        ("5.5", {"result": "Invalid", "error": "Not an integer"}, None),
        ("-5.5", {"result": "Invalid", "error": "Not an integer"}, None),
        ("-a", {"result": "Invalid", "error": "Not an integer"}, None),
    ]
)
@pytest.mark.asyncio
async def test_batch_count(mflx_serial, batch_count, expected_result, expected_payload):
    """Test the batch_count method with various arguments."""

    # Mock the _send_message method
    async def mock_send_message(sent_message, payload, addr):
        if sent_message.id == SentMessageId.BATCH_COUNT and payload is None:
            return {"result": "data", "count": 10, "total": 100}  # Simulated GET response
        return {"result": "OK"}  # Simulated SET response

    mflx_serial._send_message = MagicMock(side_effect=mock_send_message)

    # Call the method and capture the result
    result = await mflx_serial.batch_count(batch_count)
    assert result == expected_result

    if batch_count is None:  # Case 1: GET batch count
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, _ = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.BATCH_COUNT
        assert sent_message.msg_type == SentMessageType.RESP_GET
        assert payload == expected_payload
    elif expected_payload is not None:  # Case 2: Valid SET batch count
        mflx_serial._send_message.assert_called_once()
        sent_message, payload, _ = mflx_serial._send_message.call_args[0]
        assert sent_message.id == SentMessageId.BATCH_COUNT
        assert sent_message.msg_type == SentMessageType.RESP_SET
        assert payload == expected_payload
    else:  # Case 3: Invalid input
        mflx_serial._send_message.assert_not_called()
