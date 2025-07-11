import asyncio
from mavsdk import System
from mavsdk.manual_control import ManualControlResult

# --- AYARLANABİLİR PARAMETRELER ---
# Uygulanacak gaz yüzdesi (0.0 = 0%, 1.0 = 100%).
THROTTLE_VALUE = 0.15
# Gazın uygulanacağı süre (saniye).
DURATION_S = 2

async def run():
    """
    Drone'a bağlanır, arm eder ve belirli bir süre boyunca
    doğrudan gaz (throttle) kontrolü uygular.
    """
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    print("Drone'a bağlanılıyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Bağlantı başarılı!")
            break

    # Uçuş kontrolcüsünün manuel kontrole hazır olduğundan emin ol
    print("Manuel kontrol için uçuş modunun 'Stabilize' veya 'Acro' olduğundan emin olun.")
    print("İlk denemeyi MUTLAKA pervaneler olmadan yapın!")
    await asyncio.sleep(3)

    print("Arm ediliyor...")
    await drone.action.arm()
    await asyncio.sleep(1)

    print("Manuel kontrol başlatılıyor...")
    # Manuel kontrolü etkinleştir
    await drone.manual_control.start_position_control()

    print(f"{DURATION_S} saniye boyunca gaz %{int(THROTTLE_VALUE * 100)} olarak ayarlanıyor...")
    
    # Manuel kontrol komutunu gönder
    # set_manual_control_input(x, y, z, r)
    # x: pitch (ileri/geri, -1 ile 1 arası)
    # y: roll (sağ/sol, -1 ile 1 arası)
    # z: yaw (dönüş hızı, -1 ile 1 arası)
    # r: throttle (gaz, 0 ile 1 arası)
    await drone.manual_control.set_manual_control_input(0.0, 0.0, 0.0, THROTTLE_VALUE)
    
    # Belirtilen süre boyunca bekle
    await asyncio.sleep(DURATION_S)
    
    print(f"{DURATION_S} saniye doldu. Gaz kesiliyor...")
    # Güvenlik için gazı sıfırla
    await drone.manual_control.set_manual_control_input(0.0, 0.0, 0.0, 0.0)
    await asyncio.sleep(1)

    print("Disarm ediliyor...")
    await drone.action.disarm()
    
    print("Görev tamamlandı.")

if __name__ == "__main__":
    asyncio.run(run())