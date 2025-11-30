#!/usr/bin/env python3
#
# app.py
# Flask ile canlı video akışı sunucusu.
# Laptop kamerasından 3D takip analizi yapar ve sonucu web'de yayınlar.
#

from flask import Flask, render_template, Response
import cv2
import numpy as np
from ultralytics import YOLO

# --- Önceki kodumuzdaki ayarlanabilir parametreler ---
TARGET_CENTER_X = 0.5
DEAD_ZONE_X = 0.05
TARGET_AREA_RATIO = 0.06
DEAD_ZONE_AREA = 0.005
TARGET_CENTER_Y = 0.5
DEAD_ZONE_Y = 0.05
CONFIDENCE_THRESHOLD = 0.5

# Flask uygulamasını başlat
app = Flask(__name__)

# YOLO modelini ve kamerayı global olarak yükleyelim ki her istekte tekrar yüklenmesin
print("YOLOv8s modeli yükleniyor...")
yolo_model = YOLO('yolov8s.pt')
print("Model başarıyla yüklendi.")

camera = cv2.VideoCapture(0)
if not camera.isOpened():
    raise IOError("HATA: Laptop kamerasına erişilemedi.")
print("Laptop kamerası başarıyla başlatıldı.")

def generate_frames():
    """Kameradan kareleri okur, işler ve web'e gönderilecek formata dönüştürür."""
    while True:
        # 1. Kameradan bir kare oku
        success, frame = camera.read()
        if not success:
            print("Kameradan görüntü alınamadı.")
            break
        
        frame_height, frame_width, _ = frame.shape

        # 2. Görüntüyü işle (YOLO Tespiti ve Durum Analizi)
        results = yolo_model(frame, classes=[0], verbose=False)
        annotated_frame = results[0].plot()

        person_info = None
        largest_area = 0
        for r in results:
            for box in r.boxes:
                if float(box.conf[0]) > CONFIDENCE_THRESHOLD:
                    x1, y1, x2, y2 = box.xyxy[0]
                    area = (x2 - x1) * (y2 - y1)
                    if area > largest_area:
                        largest_area = area
                        person_info = {
                            "center_x_ratio": float((x1 + x2) / 2 / frame_width),
                            "center_y_ratio": float((y1 + y2) / 2 / frame_height),
                            "area_ratio": float(area / (frame_width * frame_height))
                        }
        
        status_lines = []
        if person_info is None:
            status_lines.append("Durum: Kisi bulunamadi")
            status_lines.append("Eylem: Havada bekle")
        else:
            error_x = TARGET_CENTER_X - person_info["center_x_ratio"]
            if abs(error_x) < DEAD_ZONE_X: status_lines.append("Yanal: Merkezde")
            elif error_x > 0: status_lines.append("Yanal: Saga Hizalaniyor")
            else: status_lines.append("Yanal: Sola Hizalaniyor")

            error_area = TARGET_AREA_RATIO - person_info["area_ratio"]
            if abs(error_area) < DEAD_ZONE_AREA: status_lines.append("Mesafe: Ideal")
            elif error_area > 0: status_lines.append("Mesafe: Yaklasiliyor")
            else: status_lines.append("Mesafe: Uzaklasiliyor")

            error_y = TARGET_CENTER_Y - person_info["center_y_ratio"]
            if abs(error_y) < DEAD_ZONE_Y: status_lines.append("Dikey: Merkezde")
            elif error_y > 0: status_lines.append("Dikey: Alcaliniyor")
            else: status_lines.append("Dikey: Yukseliniyor")

        y0, dy = 40, 30
        for i, line in enumerate(status_lines):
            y = y0 + i * dy
            cv2.putText(annotated_frame, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        
        # 3. Kareyi JPEG formatına çevir
        (flag, encodedImage) = cv2.imencode(".jpg", annotated_frame)
        if not flag:
            continue
        
        # 4. Kareyi "yield" ile HTTP response olarak gönder
        # Bu, "Motion JPEG" (MJPEG) akışını oluşturur
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
              bytearray(encodedImage) + b'\r\n')

@app.route("/")
def index():
    """Ana sayfayı render eder."""
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    """Video akışını sağlayan yol. generate_frames fonksiyonunu çalıştırır."""
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    # Sunucuyu başlat. host='0.0.0.0' ile ağdaki diğer cihazlardan erişilebilir hale getir.
    app.run(host='0.0.0.0', port=5000, debug=True)