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

    print("enable              : Enable Pump's Serial Comms module")
    print("disable             : Disable Pump's Serial Comms module")
    print("status              : Get the status of the pump")
    print("dispense-status     : Get dispense status")
    print("start               : Start pump")
    print("stop                : Stop pump")
    print("dir-cw              : Set pump's direction to Clockwise")
    print("dir-ccw             : Set pump's direction to Counter-clockwise")
    print("speedp              : Get the pump's speed in percentage")
    print("speedp XX.X         : Set the pump's speed in percentage")
    print("speedr              : Get the pump's speed in RPM")
    print("speedr XX.XX        : Set pump's speed in RPM ")
    print("volume              : Get pump volume in current unit set")
    print("volume-rev          : Get pump volume in rev")
    print("unit-index          : Get the pump's flow unit index")
    print("unit-index XX       : Set the pump's flow unit index")
    print("id [id]             : Set the pump id")
    print("reset-cumulative    : Reset pump's cumulative volume to zero")
    print("panel-active        : Sets control panel to manual operation")
    print("panel-inactive      : Sets control panel to inactive")
    print("mode-continuous     : Set dispense mode to continuous")
    print("mode-time           : Set dispense mode to time")
    print("on-time             : Get the pump on-time in full")
    print("on-time HH:MM:SS.s  : Set the pump on-time in full")
    print("on-time-ds          : Get the pump on-time in 1/10 seconds")
    print("on-time-ds XXXX     : Set the pump on-time in 1/10 seconds")
    print("on-time-m XXX       : Set pump on time in minutes")
    print("on-time-hr XX       : Set pump on time in hours")
    print("off-time            : Get off-time in full")
    print("off-time HH:MM:SS.s : Set off-time in full")
    print("software-version    : Get the software version of the pump")
    print('model-serial-version: Get the pump model and serial version of the pump')
    print("store-configs       : Set pump configurations to current values")
    print("restore-configs     : Set pump configurations to default values")
    print("batch-count         : Get the pump's Batch Count.")
    print("batch-total XXXXX   : Set the pump's Batch Total.")
    print("reset-batch         : Reset batch count to zero")
    print("q, quit,exit        : to quit the program")
    print("?, h , help         : for help")


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

            elif args[0] == 'on-time':
                print(PREFIX + "Get on-time in full")
                response = await pump.on_time_full()
            elif args[0] == "panel-active":
                print(PREFIX + "Sets control panel to manual operation.")
                response = await pump.set_panel_active(True)

            elif args[0] == "panel-inactive":
                print(PREFIX + "Sets control panel to inactive.")
                response = await pump.set_panel_active(False)

            elif args[0] == 'mode-continuous':
                print(PREFIX + "Set dispense mode to continuous")
                response = await pump.set_dispense_mode('continuous')

            elif args[0] == 'mode-time':
                print(PREFIX + "Set dispense mode to time")
                response = await pump.set_dispense_mode('time')

            elif args[0] == 'software-version':
                print(PREFIX + "Get software version of the pump")
                response = await pump.get_software_version()

            elif args[0] == 'model-serial-version':
                print(PREFIX + "Get the pump model and serial version of the pump")
                response = await pump.get_version__model()

            elif args[0] == "store-configs":
                print(PREFIX + "Storing pump configurations...")
                response = await pump.store_configs()

            elif args[0] == "restore-configs":
                print(PREFIX + "Restoring pump configurations to default...")
                response = await pump.restore_configs()

            elif args[0] == 'reset-batch':
                print(PREFIX + "Reset batch count to zero")
                response = await pump.reset_batch()
            elif args[0] == 'on-time-ds':
                print(PREFIX + "Get on-time in 1/10 seconds")
                response = await pump.on_time_decisecond()

            elif args[0] == 'dispense-status':
                print(PREFIX + "Get dispense status")
                response = await pump.dispense_status()

            elif args[0] == 'batch-count':
                print(PREFIX + "Get batch count")
                response = await pump.batch_count()

            elif args[0] in ['q', 'Q', 'quit', 'exit']:
                try:
                    exit(0)
                except Exception as ex:
                    print("Exit program with exception %s" % ex)

            elif args[0] == 'off-time':
                print(PREFIX + "Get off-time in full")
                response = await pump.off_time_full()

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

            elif args[0] == 'on-time':
                print(PREFIX + "set on-time in full")
                response = await pump.on_time_full(args[1])
            elif args[0] == 'off-time':
                print(PREFIX + "Set off-time in full")
                response = await pump.off_time_full(args[1])

            elif args[0] == 'on-time-m':
                print(PREFIX + "Set pump on time in minutes")
                response = await pump.on_time_min(args[1])

            elif args[0] == 'on-time-hr':
                print(PREFIX + "Set pump on time in hours")
                response = await pump.on_time_hr(args[1])
            elif args[0] == 'on-time-ds':
                print(PREFIX + "Set on-time in 1/10 seconds")
                response = await pump.on_time_decisecond(args[1])

            elif args[0] == 'batch-total':
                print(PREFIX + "Set batch total")
                response = await pump.batch_count(args[1])

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
