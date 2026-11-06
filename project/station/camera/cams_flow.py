import threading
import cv2
from project.station.camera.frame_settings import apply_settings_to_frame
from project.configuration.worker import read_from_json, write_to_json
import base64

def cam_capture(cam_id: int):
    cap = cv2.VideoCapture(cam_id)
    while True:
        # Захват изображения с подключенной камеры,
        # его кодирование в Base64 и трансляция в левом окне
        ret, frame = cap.read()
        frame = apply_settings_to_frame(frame)
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
        break
    return
