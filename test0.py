import asyncio
from mavsdk import System
from mavsdk.manual_control import ManualControlError

# --- AYARLANABİLİR PARAMETRELER ---
THROTTLE_VALUE = 0.20
DURATION_S = 10

async def run():
    """
    Drone'a bağlanır, arm eder ve belirli bir süre boyunca
    doğrudan gaz (throttle) kontrolü uygular. (DÜZELTİLMİŞ VERSİYON)
    """
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    print("Drone'a bağlanılıyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Bağlantı başarılı!")
            break

    print("Manuel kontrol için uçuş modunun 'Stabilize' veya 'Acro' olduğundan emin olun.")
    print("İlk denemeyi MUTLAKA pervaneler olmadan yapın!")
    await asyncio.sleep(3)

    print("Arm ediliyor...")
    await drone.action.arm()
    await asyncio.sleep(1)

    # --- DÜZELTİLMİŞ SIRALAMA ---
    
    # 1. ÖNCE, GÜVENLİ BİR BAŞLANGIÇ POZİSYONU AYARLA (HER ŞEY SIFIR)
    print("Manuel kontrol için başlangıç pozisyonu ayarlanıyor (gaz=0)...")
    await drone.manual_control.set_manual_control_input(0.0, 0.0, 0.0, 0.0)
    
    # 2. ŞİMDİ, MANUEL KONTROLÜ BAŞLAT
    print("Manuel kontrol başlatılıyor...")
    try:
        await drone.manual_control.start_position_control()
    except ManualControlError as e:
        print(f"Manuel kontrol başlatılamadı: {e}")
        print("Lütfen drone'un 'Stabilize' veya 'Acro' modunda olduğundan emin olun.")
        await drone.action.disarm()
        return

    # 3. KONTROL BAŞLADI, İSTENEN GAZI GÖNDER
    print(f"{DURATION_S} saniye boyunca gaz %{int(THROTTLE_VALUE * 100)} olarak ayarlanıyor...")
    await drone.manual_control.set_manual_control_input(0.0, 0.0, 0.0, THROTTLE_VALUE)
    
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
