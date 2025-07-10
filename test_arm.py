import asyncio
from mavsdk import System

async def run():
    """
    Drone'a bağlanır, 'arm' komutunu gönderir ve 15 saniye sonra
    otomatik olarak kapanır.
    """
    # Drone'a bağlan
    drone = System()
    await drone.connect(system_address="serial:///dev/serial0:57600")

    print("Drone'a bağlanılmaya çalışılıyor...")
    
    # Bağlantının kurulmasını bekle
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Bağlantı başarılı! Drone keşfedildi.")
            break
            
    print("Drone'a arm komutu gönderiliyor...")
    
    try:
        # Arm komutunu gönder
        await drone.action.arm()
        print("Arm komutu başarıyla gönderildi. Pervaneler dönmeye başlamalı.")
        
    except Exception as e:
        # Arm etme sırasında oluşabilecek hataları yakala
        print(f"Arm etme sırasında bir hata oluştu: {e}")
        return

    # Programın 5 saniye boyunca 'arm' durumunda kalmasını sağla
    print("\nDrone 'arm' durumunda. Program 5 saniye sonra otomatik olarak sonlanacak.")
    await asyncio.sleep(5)

    print("5 saniye doldu. Drona disarm komudu gönderiliyor...")
    try:
        # Disarm komutunu gönder
        await drone.action.disarm()
        print("Disarm komutu başarıyla gönderildi. Pervaneler duracak.")
    except Exception as e:
        print(f"Disarm etme sırasında bir hata oluştu: {e}")


if __name__ == "__main__":
    # Programı çalıştır
    asyncio.run(run())
