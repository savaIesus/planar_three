import cv2
import os
import base64
import numpy

from pandas.io.formats.style import buffering_args
from torchgen.native_function_generation import self_to_out_signature
from ultralytics import YOLO

from project.application.layers.networks_list import middle, near, far # общие названия камер
from project.station.math import bounding_rectangular, text_placement
from project.configuration.worker import read_from_json, write_to_json
from project.alghorithms.network import process_frame
import threading

from project.station.weights.networks_vault import ModelsVault
lock = threading.Lock()



def draw_contour(frame, cam_id, models):
    """
    Передаёт кадр и модель нейросети в обработку, получая изображение с наложенными контурами.

    Параметры:
    frame (numpy.ndarray): Кадр изображения.
    Model: Модель для предсказания объектов.
    cam_id: номер камеры

    Возвращает:
    tuple:
        - numpy.ndarray: Обработанный кадр.
        - list: Список объектов в формате
          [{"name": str, "class": int, "color": tuple, "center": (int, int), "conf": float}].
    """

    encoded_image = ''
    object_data = []
    if isinstance(frame, str):
        try:
            img_data = base64.b64decode(frame)
            npa_r = numpy.frombuffer(img_data, numpy.uint8)
            frame = cv2.imdecode(npa_r, cv2.IMREAD_COLOR)
            if frame is None:
                print("Не удалось декодировать изображение из base64")
                return encoded_image, object_data
        except Exception as ex:
            print(f"Ошибка декодирования изображения: {ex}")
            return encoded_image, object_data

    if frame is None or frame.size == 0:
        print("Получено пустое или невалидное изображение")
        return encoded_image, object_data


    if cam_id == 2:
        cam_key = middle
    elif cam_id == 1:
        cam_key = far
    elif cam_id == 0:
        cam_key = near
    else:
        print(f"Неизвестный cam_id: {cam_id}")
        return encoded_image, object_data

    model_list = models.get(cam_key, [] )

    if not model_list: # на случай если вообще не прописаны нейронки
        _, buffer = cv2.imencode(".jpg", frame)
        encoded_image = base64.b64encode(buffer.tobytes()).decode("utf-8")
        return encoded_image, object_data

    for m, color, _, conf in model_list:
        if m is None:
            continue

        bgr_color = [color[2], color[1], color[0]]
        encoded_image, iteration_data = process_frame(frame, m, bgr_color, float(conf), draw_area=0)
        if iteration_data:
            object_data.append(iteration_data.copy())
    return encoded_image, object_data
