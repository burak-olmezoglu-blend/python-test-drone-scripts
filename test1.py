from mavsdk import System
import asyncio

async def test_connection():
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600") # serial:///dev/ttyAMA0:57600 ya da serial:///dev/serial0:57600 ya da udp://:14551
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Bağlantı başarılı!")
            break

asyncio.run(test_connection())
