"""Create a command line for testing MasterflexSerial Communication from PC side."""
import asyncio
import os
import signal
import sys
from sys import exit

from masterflexserial.masterflexserial import MasterflexSerial
from console import cmd


def cmd_help():
    """Display the supported commands and how to use them."""
    print("Supported commands:")

    print("enable          : Enable Pump's Serial Comms module")
    print("disable         : Disable Pump's Serial Comms module")
    print("status          : Get the status of the pump")
    print("start           : Start pump")
    print("stop            : Stop pump")
    print("dir-cw          : Set pump's direction to Clockwise")
    print("dir-ccw         : Set pump's direction to Counter-clockwise")
    print("reset-cumulative: Reset pump's cumulative volume to zero")
    print("speedp          : Get the pump's speed in percentage")
    print("speedp XX.X     : Set the pump's speed in percentage")
    print("speedr          : Get the pump's speed in RPM")
    print("speedr XX.XX    : Set pump's speed in RPM ")
    print("volume          : Get pump volume in current unit set")
    print("volume-rev      : Get pump volume in rev")
    print("unit-index      : Get the pump's flow unit index")
    print("unit-index XX   : Set the pump's flow unit index")
    print("id [id]         : Set the pump id")
    print("q, quit,exit    : to quit the program")
    print("?, h , help     : for help")


PREFIX = "mflx# "


async def console_cmd(pump: MasterflexSerial):
    """Run the loop to get input text.

    pump: an instance of the MasterflexSerial class

    """
    # Wait here for 1 second to wait for the Serial Comm to connect
    await asyncio.sleep(1)

    print("Masterflex Pump Drive Command Line Tools")

    while True:
        print(PREFIX, end='', flush=True)
        x = await cmd.ainput()
        args = cmd.get_params(x)
        argument = ' '.join(map(str, args))
        response = None

        if len(args) == 1:

            if args[0] == 'enable':
                print(PREFIX + "Enable pump serial communication")
                response = await pump.enable()

            elif args[0] == 'disable':
                print(PREFIX + "Disable pump serial communication")
                response = await pump.disable()

            elif args[0] == 'start':
                print(PREFIX + "Start pump")
                response = await pump.start()

            elif args[0] == 'stop':
                print(PREFIX + "Stop pump")
                response = await pump.stop()

            elif args[0] == 'status':
                print(PREFIX + "Get the pump status")
                response = await pump.status()

            elif args[0] == 'dir-cw':
                print(PREFIX + "Set pump direction to 'clockwise'")
                response = await pump.set_dir('cw')

            elif args[0] == 'dir-ccw':
                print(PREFIX + "Set pump direction to 'counter-clockwise'")
                response = await pump.set_dir('ccw')

            elif args[0] == 'reset-cumulative':
                print(PREFIX + "Reset pump cumulative volume to zero")
                response = await pump.reset_cumulative()

            elif args[0] == 'speedr':
                print(PREFIX + "Get pump speed in RPM")
                response = await pump.speed_rpm()

            elif args[0] == 'speedp':
                print(PREFIX + "Get Pump speed in percentage")
                response = await pump.speed_percent()

            elif args[0] == 'volume':
                print(PREFIX + "Get Pump volume in current unit")
                response = await pump.volume()

            elif args[0] == 'volume-rev':
                print(PREFIX + "Get Pump volume in rev")
                response = await pump.volume_rev()

            elif args[0] == 'unit-index':
                print(PREFIX + "Get pump flow rate unit index")
                response = await pump.unit_index()

            elif args[0] in ['q', 'Q', 'quit', 'exit']:
                try:
                    exit(0)
                except Exception as ex:
                    print("Exit program with exception %s" % ex)

            elif args[0] in ['?', 'h', 'help']:
                cmd_help()

            else:
                print(PREFIX + args[0] + ": command is not supported")

        elif len(args) == 2:
            if args[0] == 'speedp':
                print(PREFIX + "Set pump speed in percentage")
                response = await pump.speed_percent(args[1])

            elif args[0] == 'id':
                print(PREFIX + "Set the pump IPC Serial ID " + args[1])
                response = await pump.set_addr(args[1])

            elif args[0] == 'speedr':
                print(PREFIX + "Set pump speed in RPM")
                response = await pump.speed_rpm(args[1])

            elif args[0] == 'unit-index':
                print(PREFIX + "Set pump flow rate unit index")
                response = await pump.unit_index(args[1])

            else:
                print(PREFIX + argument + ": command is not supported")

        else:
            print(PREFIX + argument + ": command is not supported")

        if response is not None:
            print(response)


async def main(port="/dev/ttyUSB0"):
    """Run the main program."""
    pump = MasterflexSerial(port, "1")
    serial_task = asyncio.create_task(pump.connect())
    cmd_task = asyncio.create_task(console_cmd(pump))
    loop = asyncio.get_event_loop()

    if os.name != 'nt':
        # Support Linux/iOS operating system
        signals = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)
        for signum in signals:
            loop.add_signal_handler(signum, serial_task.cancel)
            loop.add_signal_handler(signum, cmd_task.cancel)

    try:
        await asyncio.gather(serial_task, cmd_task)
    finally:
        if cmd_task.done() and not cmd_task.cancelled():
            cmd_task.exception()
        if serial_task.done() and not serial_task.cancelled():
            serial_task.exception()


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Usage: python3 masterflex.py <serial_path>")

    else:
        asyncio.run(main(sys.argv[1]))
