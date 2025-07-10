#!/usr/bin/env python3
from mavsdk import System
import asyncio

async def basic_takeoff_land():
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600") # serial:///dev/ttyAMA0:57600 
    
    print("Bağlantı bekleniyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Pixhawk'a bağlanıldı!")
            break
    
    print("Arm yapılıyor...")
    await drone.action.arm()
    
    print("0.5 metre yüksekliğe kalkış yapılıyor...")
    await drone.action.set_takeoff_altitude(0.5)
    await drone.action.takeoff()
    
    # 10 saniye bekleyelim (0.5 metre yükseklikte)
    await asyncio.sleep(15)
    
    print("İniş yapılıyor...")
    await drone.action.land()
    
    print("Test tamamlandı!")

asyncio.run(basic_takeoff_land())
