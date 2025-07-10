import asyncio
import numpy as np
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed

# --- AYARLANABİLİR KONTROLCÜ PARAMETRELERİ ---
# Bu kazanç değeri, drone'un ne kadar agresif tepki vereceğini belirler.
# Düşük değerler daha yavaş ama kararlı, yüksek değerler daha hızlı ama salınımlı olabilir.
KP_VERTICAL = 1.0 
# Drone'un hedefe ne kadar yaklaştığında "ulaştım" sayacağını belirler (metre).
ALTITUDE_TOLERANCE = 0.05 
# Drone'un maksimum dikey hızı (m/s).
MAX_VERTICAL_SPEED = 1.0

async def run():
    """1m kalk, P-Kontrolcü ile 1m daha hassas yüksel, in."""
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    print("Drone'a bağlanıldı!")
    await drone.action.arm()
    print("Arm edildi.")

    await drone.action.set_takeoff_altitude(1.0)
    await drone.action.takeoff()
    print("1 metreye kalkış yapılıyor...")
    await asyncio.sleep(15)

    # Başlangıç ve hedef irtifayı belirle
    async for position in drone.telemetry.position():
        start_alt = position.relative_altitude_m
        break
    
    target_alt = start_alt + 1.0
    print(f"Başlangıç irtifası: {start_alt:.2f} m. Hedef irtifa: {target_alt:.2f} m.")
    
    # Offboard modunu başlat
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await drone.offboard.start()
    print("Offboard modu başlatıldı. Hassas yükseliş başlıyor...")

    # P-Kontrolcü Döngüsü
    while True:
        async for position in drone.telemetry.position():
            current_alt = position.relative_altitude_m
            break

        # Hedefe olan uzaklığı (hatayı) hesapla
        error = target_alt - current_alt
        
        # Eğer hedefe çok yakınsak döngüyü bitir
        if abs(error) < ALTITUDE_TOLERANCE:
            print(f"Hedef irtifaya {ALTITUDE_TOLERANCE}m tolerans ile ulaşıldı.")
            break

        # P-Kontrolcü: Hızı hatayla orantılı olarak belirle
        # Yükselmek için negatif hız gerektiğinden sonuç eksi ile çarpılır.
        vertical_speed = -KP_VERTICAL * error
        
        # Hızı limitle
        vertical_speed = np.clip(vertical_speed, -MAX_VERTICAL_SPEED, MAX_VERTICAL_SPEED)

        print(f"Mevcut İrtifa: {current_alt:.2f}m, Hedef Hız: {vertical_speed:.2f} m/s", end="\r")
        await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, vertical_speed, 0.0))
        
        await asyncio.sleep(0.1) # Kontrol döngüsü frekansı

    print("\nHedefe ulaşıldı. Haraket durduruluyor.")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(5)
    
    print("Offboard modundan çıkılıyor.")
    await drone.offboard.stop()
    
    print("İniş yapılıyor...")
    await drone.action.land()

if __name__ == "__main__":
    asyncio.run(run())
