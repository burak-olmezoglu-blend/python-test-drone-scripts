import asyncio
import numpy as np
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed

# --- AYARLANABİLİR KONTROLCÜ PARAMETRELERİ ---
KP_VERTICAL = 1.0 
ALTITUDE_TOLERANCE = 0.05 
MAX_VERTICAL_SPEED = 1.0

async def run():
    """2m kalk, P-Kontrolcü ile 1m hassas alçal, in."""
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    print("Drone'a bağlanıldı!")
    await drone.action.arm()
    print("Arm edildi.")

    await drone.action.set_takeoff_altitude(2.0)
    await drone.action.takeoff()
    print("2 metreye kalkış yapılıyor...")
    await asyncio.sleep(15)

    # Başlangıç ve hedef irtifayı belirle
    async for position in drone.telemetry.position():
        start_alt = position.relative_altitude_m
        break
        
    target_alt = start_alt - 1.0 # Hedefimiz 1 metre daha alçak
    print(f"Başlangıç irtifası: {start_alt:.2f} m. Hedef irtifa: {target_alt:.2f} m.")
    
    # Offboard modunu başlat
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await drone.offboard.start()
    print("Offboard modu başlatıldı. Hassas alçalma başlıyor...")

    # P-Kontrolcü Döngüsü
    while True:
        async for position in drone.telemetry.position():
            current_alt = position.relative_altitude_m
            break

        error = target_alt - current_alt
        
        if abs(error) < ALTITUDE_TOLERANCE:
            print(f"Hedef irtifaya {ALTITUDE_TOLERANCE}m tolerans ile ulaşıldı.")
            break

        vertical_speed = -KP_VERTICAL * error
        vertical_speed = np.clip(vertical_speed, -MAX_VERTICAL_SPEED, MAX_VERTICAL_SPEED)

        print(f"Mevcut İrtifa: {current_alt:.2f}m, Hedef Hız: {vertical_speed:.2f} m/s", end="\r")
        await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, vertical_speed, 0.0))
        
        await asyncio.sleep(0.1)

    print("\nHedefe ulaşıldı. Haraket durduruluyor.")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(5)
    
    print("Offboard modundan çıkılıyor.")
    await drone.offboard.stop()
    
    print("İniş yapılıyor...")
    await drone.action.land()

if __name__ == "__main__":
    asyncio.run(run())
