import asyncio
import numpy as np
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed

# --- AYARLANABİLİR KONTROLCÜ PARAMETRELERİ ---
# Yönelim (Yaw) için oransal kazanç. Dönüşün ne kadar "akıllı" yavaşlayacağını belirler.
KP_YAW = 0.8
# İzin verilen maksimum dönüş hızı (derece/saniye).
MAX_YAW_SPEED_DEG_S = 45.0
# Hedef açıya kaç derece kala "ulaştım" sayılacağı. Hassasiyeti belirler.
YAW_TOLERANCE_DEG = 1.0
# Kalkış ve dönüş için kullanılacak irtifa (metre).
ROTATION_ALTITUDE = 2.0

async def run():
    """Drone'u kaldırır, P-Kontrolcü ile saat yönünde hassas 360 derece döndürür ve iner."""
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    print("Drone'a bağlanıldı!")
    await drone.action.arm()
    print("Arm edildi.")

    await drone.action.set_takeoff_altitude(ROTATION_ALTITUDE)
    await drone.action.takeoff()
    print(f"{ROTATION_ALTITUDE} metreye kalkış yapılıyor...")
    await asyncio.sleep(15)

    async for heading in drone.telemetry.heading():
        last_heading_deg = heading.heading_deg
        break
    
    print(f"Hassas dönüşe başlanıyor. Başlangıç açısı: {last_heading_deg:.2f} derece.")
    
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await drone.offboard.start()

    total_rotation_deg = 0.0
    target_rotation_deg = 360.0

    # Yönelim için P-Kontrolcü Döngüsü
    while True:
        async for heading in drone.telemetry.heading():
            current_heading_deg = heading.heading_deg
            break

        # Açısal farkı hesapla (360/0 derece geçişini düzelterek)
        delta_heading = current_heading_deg - last_heading_deg
        if delta_heading > 180: delta_heading -= 360
        elif delta_heading < -180: delta_heading += 360
        
        total_rotation_deg += delta_heading
        last_heading_deg = current_heading_deg

        # Kalan açıyı (hatayı) hesapla
        error_deg = target_rotation_deg - total_rotation_deg
        
        # Eğer hedefe çok yakınsak döngüyü bitir
        if abs(error_deg) < YAW_TOLERANCE_DEG:
            break
            
        # P-Kontrolcü: Dönüş hızını kalan açıyla orantılı olarak belirle
        yaw_speed = KP_YAW * error_deg
        # Hızı limitle
        yaw_speed = np.clip(yaw_speed, -MAX_YAW_SPEED_DEG_S, MAX_YAW_SPEED_DEG_S)

        print(f"Dönülen Açı: {total_rotation_deg:.2f}° | Kalan Açı: {error_deg:.2f}° | Anlık Hız: {yaw_speed:.2f}°/s", end="\r")
        await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, yaw_speed))
        
        await asyncio.sleep(0.05) # Kontrol döngüsünü daha hassas hale getirelim (20Hz)

    print(f"\n360 derece dönüş {YAW_TOLERANCE_DEG}° tolerans ile tamamlandı. Haraket durduruluyor.")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(5)
    
    print("Offboard modundan çıkılıyor.")
    await drone.offboard.stop()
    
    print("İniş yapılıyor...")
    await drone.action.land()

if __name__ == "__main__":
    asyncio.run(run())
