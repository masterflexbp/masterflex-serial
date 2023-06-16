import asyncio
import sys
from masterflexserial.masterflexserial import MasterflexSerial

async def start(port):

    pump = MasterflexSerial(port, "1")
    serial_task = asyncio.create_task(pump.connect())

    async def pump_cmd():
        await asyncio.sleep(1)
        await pump.start()

    cmd_task = asyncio.create_task(pump_cmd())
    # Run both task at the same time
    await asyncio.gather(serial_task, cmd_task)

asyncio.run(start(sys.argv[1]))