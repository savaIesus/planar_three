import cv2
import base64
import numpy
import threading


from project.station.math import contour_edge_distances, text_placement
from project.alghorithms.models_alg import result_of_detect, default_models, flatness_model
from project.configuration.worker import read_from_path

locker = threading.Lock()

def process_frame(frame,model,color: list, conf, draw_area=0):
    """
    Обрабатывает кадр, применяя модель для обнаружения объектов, и возвращает кадр с наложенными полигонами,
    а также список объектов с их названиями, классами, площадями, центрами масс и средними значениями пикселей.

    Параметры:
    frame (numpy.ndarray): Кадр изображения.
    Model: Модель для предсказания объектов.

    Возвращает:
    tuple:
        - numpy.ndarray: Обработанный кадр.
        - list: Список объектов в формате
          [{"name": str, "class": int, "area": float, "center": (int, int), "mean_pixel_value": float}].
    """
    try:
        object_data = []
        # Обработка изображения моделью
        results_detect = model.predict(frame,device='cpu', iou=0, conf=conf, imgsz=1280, verbose=False,task="segment")

        # Обработка результатов детекции
        if results_detect[0].masks is not None and len(results_detect[0].masks.xy) > 0:
            segments, classes, names = result_of_detect(results_detect)

            if names[0] == 'flatness':
                heights = read_from_path(r'project\configuration\heights_cfg.json')
                object_data = flatness_model(segments, classes, names, frame, color, draw_area, heights)
            else:
                object_data = default_models(segments, classes, names, frame, color, draw_area)


        # Кодируем изображение в JPEG
        encode_status, buffer = cv2.imencode('.jpg', frame)
        if not encode_status:
            print('Не удалось закодировать изображение')
            return None, object_data if object_data else []
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        with locker:
            print(f'{color} - {object_data}')

    except Exception as ex:
        print(f'Ошибка распознавания модели {ex}')
        encoded_image = None

    return encoded_image, object_data
