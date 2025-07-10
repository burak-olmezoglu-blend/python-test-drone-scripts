import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityBodyYawspeed
from math import radians, cos, sin, asin, sqrt

# --- Mesafe Hesaplama ---
def haversine_distance(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1; dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)); r = 6371000
    return c * r

async def run():
    """1m kalk, GPS ile ölçerek 1m geri git, in."""
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    print("Drone'a bağlanıldı!")
    await drone.action.arm()
    print("Arm edildi.")

    await drone.action.set_takeoff_altitude(1.0)
    await drone.action.takeoff()
    print("1 metreye kalkış yapılıyor...")
    await asyncio.sleep(15)

    # Başlangıç pozisyonunu al (GPS)
    start_pos = None
    async for position in drone.telemetry.position():
        start_pos = position
        print(f"Başlangıç GPS: {start_pos.latitude_deg:.7f}, {start_pos.longitude_deg:.7f}")
        break
    
    # Offboard modunu başlat
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await drone.offboard.start()
    print("Offboard modu başlatıldı.")

    # Geri hareketi başlat
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(-1.0, 0.0, 0.0, 0.0)) # 1 m/s hızla geri
    
    # Hedef mesafeye ulaşana kadar bekle
    target_distance = 1.0
    while True:
        async for position in drone.telemetry.position():
            current_pos = position
            break
        
        distance_traveled = haversine_distance(start_pos.longitude_deg, start_pos.latitude_deg, 
                                               current_pos.longitude_deg, current_pos.latitude_deg)
        print(f"Kat edilen yatay mesafe: {distance_traveled:.2f} m")
        
        if distance_traveled >= target_distance:
            break
        await asyncio.sleep(0.2)

    print("Hedefe ulaşıldı. Haraket durduruluyor.")
    await drone.offboard.set_velocity_body(VelocityBodyYawspeed(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(5)
    
    print("Offboard modundan çıkılıyor.")
    await drone.offboard.stop()
    
    print("İniş yapılıyor...")
    await drone.action.land()

if __name__ == "__main__":
    asyncio.run(run())
