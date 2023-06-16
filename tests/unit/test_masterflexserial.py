"""Unit tests related to MasterflexSerial main module."""
import json
import asyncio
from unittest.mock import MagicMock

import pytest
import serial_asyncio
from asynctest import mock

from masterflexserial.masterflexserial import MasterflexSerial
from masterflexserial.message import SentMessage, SentMessageId, SentMessageType, ReceivedMessage


@pytest.mark.asyncio
async def test_serial_connection():
    """Verify that the serial client requests to create a serial connection."""
    with mock.patch.object(serial_asyncio, 'create_serial_connection',
                           return_value=asyncio.Future()) as create_serial_connection:

        mflx = MasterflexSerial("/dev/pts/1234", 115200)

        serial_transport = MagicMock()
        serial_protocol = MagicMock()
        create_serial_connection.return_value.set_result((serial_transport, serial_protocol))
        await mflx.connect()

        assert create_serial_connection.called


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
