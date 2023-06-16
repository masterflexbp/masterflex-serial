import asyncio
import sys
from masterflexserial.masterflexserial import MasterflexSerial

async def set_speedp(port, value):

    pump = MasterflexSerial(port, "1")
    serial_task = asyncio.create_task(pump.connect())

    async def pump_cmd():
        await asyncio.sleep(1)
        print (await pump.speed_percent(value))

    cmd_task = asyncio.create_task(pump_cmd())
    # Run both task at the same time
    await asyncio.gather(serial_task, cmd_task)

asyncio.run(set_speedp(sys.argv[1], sys.argv[2]))