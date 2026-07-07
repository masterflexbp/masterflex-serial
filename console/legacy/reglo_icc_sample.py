"""Sample serial script for a legacy ISMATEC REGLO ICC pump.

Usage:
    python console\\legacy\\serial_test.py COM8

This sample enables independent channel control, runs channel 1 at 20 RPM for
5 seconds, runs channel 3 at 10 RPM for 10 seconds, then stops all channels.
"""

import asyncio
import sys

from masterflexserial.masterflexserial import MasterflexSerial


# The REGLO ICC manual specifies 9600 baud, 8 data bits, no parity, 1 stop bit.
BAUD_RATE = 9600
READ_TIMEOUT = 2.0
RESPONSE_IDLE_DELAY = 0.1
STATUS_SETTLE_DELAY = 0.3
PORT_OPEN_DELAY = 1.0
CONNECT_RETRY_COUNT = 10
CONNECT_RETRY_DELAY = 0.2
MODE_RETRY_COUNT = 5
MODE_RETRY_DELAY = 0.5
COMMAND_SPACING_DELAY = 0.1

# Change this if the pump has a different legacy address.
PUMP_ADDRESS = "2"

ALL_CHANNELS = ("1", "2", "3", "4")

# Edit these values to change which channels run and at what speed.
CHANNEL_SPEEDS_RPM = {
    "1": 20.0,
    "3": 10.0,
}

# Channel 1 stops after 5 seconds. Channel 3 stops after 10 seconds.
SHORT_RUN_CHANNELS = ("1",)
SHORT_RUN_SECONDS = 5.0
LONG_RUN_CHANNELS = ("3",)
LONG_RUN_SECONDS = 10.0
OK_RESPONSE = "*"
NO_RESPONSE = ""
NO_RESPONSE_DISPLAY = "<no immediate response>"


class LegacyIccProtocol(asyncio.Protocol):
    """Raw ASCII protocol for the legacy REGLO ICC command set."""

    def __init__(self, connection_made, connection_lost, data_received):
        self.transport = None
        self.connection_made_callback = connection_made
        self.connection_lost_callback = connection_lost
        self.data_received_callback = data_received

    def connection_made(self, transport):
        """Save the serial transport when the port opens."""
        self.transport = transport
        self.connection_made_callback(self)

    def data_received(self, data):
        """Forward raw pump responses to the sample script."""
        self.data_received_callback(data)

    def connection_lost(self, exc):
        """Notify the sample when the port closes."""
        self.connection_lost_callback()


class LegacyIccSerial(MasterflexSerial):
    """MasterflexSerial connection wrapper for legacy ICC raw commands."""

    def __init__(self, port, pump_address, baud):
        super().__init__(port, pump_address, baud)
        self._response_event = asyncio.Event()
        self._response_data = bytearray()
        self._closing = False

    def _protocol_factory(self):
        """Create a raw ICC protocol instead of the newer-pump decoder."""
        return LegacyIccProtocol(
            self._connection_made,
            self._legacy_connection_lost,
            self._raw_response_received,
        )

    def _legacy_connection_lost(self):
        """Handle expected and unexpected serial connection closures."""
        self._protocol = None
        if self._closing:
            print("Disconnected.")
        else:
            print("Connection lost unexpectedly.")

    def _raw_response_received(self, data):
        """Store the most recent raw response bytes."""
        self._response_data.extend(data)
        self._response_event.set()

    def close(self):
        """Close the serial transport."""
        self._closing = True
        if self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    async def read_icc_response(self, wait_for_terminator=False):
        """Read until a full ICC response is available or the response goes idle."""
        loop = asyncio.get_event_loop()
        deadline = loop.time() + READ_TIMEOUT

        while loop.time() < deadline:
            if b"\r" in self._response_data or b"\n" in self._response_data:
                break

            timeout = deadline - loop.time()
            if self._response_data and not wait_for_terminator:
                timeout = min(timeout, RESPONSE_IDLE_DELAY)

            self._response_event.clear()
            try:
                await asyncio.wait_for(self._response_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                if self._response_data or wait_for_terminator:
                    break
                return ""

        return self._response_data.decode("ascii", "replace").strip()

    async def send_icc_command(
        self,
        command,
        wait_for_terminator=False,
        expected_response=None,
        verification_label=None,
    ):
        """Send one ICC ASCII command and return the response text and send time."""
        request = "{}\r".format(command)
        self._response_data.clear()
        self._response_event.clear()

        sent_at = asyncio.get_event_loop().time()
        self.protocol.transport.write(request.encode("ascii"))
        response = await self.read_icc_response(wait_for_terminator)
        response_for_check = normalize_response_for_check(response, expected_response)
        response_display = format_response_for_display(response)
        output = "Sent: {!r}  Received: {!r}".format(request, response_display)
        if expected_response is not None and verification_label is not None:
            if response_for_check == expected_response:
                output = "{}  [{} verified]".format(output, verification_label)
            else:
                output = "{}  [{} check returned {!r}; expected {!r}]".format(
                    output,
                    verification_label,
                    response_display,
                    expected_response,
                )
        elif response and set(response) == {OK_RESPONSE} and len(response) > 1:
            output = "{}  [accepted; combined acknowledgements]".format(output)
        print(output)
        await asyncio.sleep(COMMAND_SPACING_DELAY)
        return response_for_check, sent_at


def format_speed(speed_rpm):
    """Format ICC speed as 0.01 RPM units."""
    return "{:06d}".format(round(float(speed_rpm) * 100))


def format_speed_response(speed_rpm):
    """Format expected ICC speed query response."""
    return "{:.2f}".format(float(speed_rpm))


def format_channel_list(channels):
    """Format channel numbers for customer-readable messages."""
    channels = [str(channel) for channel in channels]
    if len(channels) == 1:
        return channels[0]
    return "{} and {}".format(", ".join(channels[:-1]), channels[-1])


def normalize_response_for_check(response, expected_response):
    """Treat one or more ICC acknowledgements as a successful '*' response."""
    if expected_response == OK_RESPONSE and response and set(response) == {OK_RESPONSE}:
        return OK_RESPONSE
    return response


def format_response_for_display(response):
    """Format raw ICC responses for customer-readable console output."""
    if response == NO_RESPONSE:
        return NO_RESPONSE_DISPLAY
    return response


async def wait_for_connection(pump):
    """Wait for the serial connection to be ready."""
    await asyncio.sleep(PORT_OPEN_DELAY)
    retries = CONNECT_RETRY_COUNT
    while not pump.connected and retries > 0:
        await asyncio.sleep(CONNECT_RETRY_DELAY)
        retries -= 1

    if not pump.connected:
        raise RuntimeError("Unable to connect to {}".format(pump.port))


async def enable_channel_control(pump):
    """Enable ICC independent channel control."""
    print("Enabling independent channel control...")
    last_response = None
    for attempt in range(1, MODE_RETRY_COUNT + 1):
        response, _sent_at = await pump.send_icc_command(
            "{}~1".format(PUMP_ADDRESS),
            expected_response=OK_RESPONSE,
        )
        if response == OK_RESPONSE:
            await asyncio.sleep(MODE_RETRY_DELAY)
            return

        last_response = response
        print("Channel-control attempt {} of {} did not complete.".format(attempt, MODE_RETRY_COUNT))
        await pump.send_icc_command(
            "{}I".format(PUMP_ADDRESS),
            expected_response=OK_RESPONSE,
        )
        await asyncio.sleep(MODE_RETRY_DELAY)

    if last_response == NO_RESPONSE:
        print("Continuing with channel commands.")
        return

    raise RuntimeError(
        "Pump did not accept independent channel control. "
        "Channels cannot be run separately until this command returns '*'."
    )


async def disable_channel_control(pump):
    """Return the pump to standard legacy addressing."""
    await pump.send_icc_command(
        "{}~0".format(PUMP_ADDRESS),
        expected_response=OK_RESPONSE,
    )


async def check_channel_control(pump, expected):
    """Check whether independent channel control is enabled."""
    await pump.send_icc_command(
        "{}~".format(PUMP_ADDRESS),
        expected_response=expected,
        verification_label="Channel control",
    )


async def set_speed(pump, channel, speed_rpm):
    """Set one ICC channel to RPM mode at the requested speed."""
    print("Setting channel {} to {} RPM...".format(channel, speed_rpm))
    speed = format_speed(speed_rpm)
    await pump.send_icc_command(
        "{}L".format(channel),
        expected_response=OK_RESPONSE,
    )
    await pump.send_icc_command(
        "{}S{}".format(channel, speed),
        expected_response=OK_RESPONSE,
    )


async def set_speeds(pump, channel_speeds):
    """Set each selected ICC channel to its requested speed."""
    for channel, speed_rpm in channel_speeds.items():
        await set_speed(pump, channel, speed_rpm)


async def check_mode_and_speed(pump, channel, speed_rpm):
    """Check one channel's mode and speed setting."""
    await pump.send_icc_command(
        "{}xM".format(channel),
        wait_for_terminator=True,
        expected_response="L",
        verification_label="Channel {} RPM mode".format(channel),
    )

    await pump.send_icc_command(
        "{}S".format(channel),
        wait_for_terminator=True,
        expected_response=format_speed_response(speed_rpm),
        verification_label="Channel {} speed".format(channel),
    )


async def check_modes_and_speeds(pump, channel_speeds):
    """Check configured mode and speed for each selected channel."""
    print("Checking channel speed settings...")
    for channel, speed_rpm in channel_speeds.items():
        await check_mode_and_speed(pump, channel, speed_rpm)


async def start_channels(pump, channels):
    """Start selected ICC channels."""
    channels = tuple(channels)
    channel_label = format_channel_list(channels)
    if len(channels) == 1:
        print("Starting channel {}...".format(channel_label))
    else:
        print("Starting channels {}...".format(channel_label))

    start_times = {}
    for channel in channels:
        _response, sent_at = await pump.send_icc_command(
            "{}H".format(channel),
            expected_response=OK_RESPONSE,
        )
        start_times[channel] = sent_at
    return start_times


async def check_running_status(pump, channels, expected):
    """Check whether selected channels report running or stopped."""
    status_text = "running" if expected == "+" else "stopped"
    print("Checking that selected channels are {}...".format(status_text))
    for channel in channels:
        await pump.send_icc_command(
            "{}E".format(channel),
            expected_response=expected,
            verification_label="Channel {} {}".format(channel, status_text),
        )


async def stop_channels(pump, channels, show_message=True):
    """Stop selected ICC channels."""
    channels = tuple(channels)
    if show_message:
        channel_label = format_channel_list(channels)
        if len(channels) == 1:
            print("Stopping channel {}...".format(channel_label))
        else:
            print("Stopping channels {}...".format(channel_label))

    for channel in channels:
        await pump.send_icc_command(
            "{}I".format(channel),
            expected_response=OK_RESPONSE,
        )


async def wait_until(deadline):
    """Sleep until an absolute event-loop deadline."""
    remaining = deadline - asyncio.get_event_loop().time()
    if remaining > 0:
        await asyncio.sleep(remaining)


async def run_commands(pump):
    """Run channel 1 for 5 seconds and channel 3 for 10 seconds."""
    await wait_for_connection(pump)
    print("Connected to {}.".format(pump.port))

    print("Initial cleanup...")
    await pump.send_icc_command(
        "{}I".format(PUMP_ADDRESS),
        expected_response=OK_RESPONSE,
    )
    await asyncio.sleep(MODE_RETRY_DELAY)

    completed = False
    try:
        await enable_channel_control(pump)
        await check_channel_control(pump, "1")
        await stop_channels(pump, ALL_CHANNELS, show_message=False)
        await set_speeds(pump, CHANNEL_SPEEDS_RPM)
        await check_modes_and_speeds(pump, CHANNEL_SPEEDS_RPM)

        start_times = await start_channels(pump, CHANNEL_SPEEDS_RPM.keys())
        await check_running_status(pump, CHANNEL_SPEEDS_RPM.keys(), "+")
        await wait_until(start_times["1"] + SHORT_RUN_SECONDS)
        print("Stopping channel 1 at {} seconds...".format(SHORT_RUN_SECONDS))
        await stop_channels(pump, SHORT_RUN_CHANNELS, show_message=False)
        await wait_until(start_times["3"] + LONG_RUN_SECONDS)
        print("Stopping channel 3 at {} seconds...".format(LONG_RUN_SECONDS))
        await stop_channels(pump, LONG_RUN_CHANNELS, show_message=False)
        await asyncio.sleep(STATUS_SETTLE_DELAY)
        await check_running_status(pump, CHANNEL_SPEEDS_RPM.keys(), "-")
        completed = True
    finally:
        print("Final cleanup...")
        await stop_channels(pump, ALL_CHANNELS, show_message=False)
        await disable_channel_control(pump)
        await check_channel_control(pump, "0")
        if completed:
            print("Done.")
        pump.close()


async def run(port):
    """Connect to the pump and run the sample command sequence."""
    pump = LegacyIccSerial(port, PUMP_ADDRESS, BAUD_RATE)
    serial_task = asyncio.create_task(pump.connect())
    cmd_task = asyncio.create_task(run_commands(pump))
    await asyncio.gather(serial_task, cmd_task)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python console\\legacy\\serial_test.py COM8")

    try:
        asyncio.run(run(sys.argv[1]))
    except RuntimeError as exc:
        raise SystemExit(str(exc))
