import cv2
import base64
import numpy
import threading


from project.station.math import contour_edge_distances, text_placement
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

    object_data = []
    # try:
    # Обработка изображения моделью
    results_detect = model.predict(frame,device='cpu', iou=0, conf=conf, imgsz=1280, verbose=False,task="segment")  # размер изображения

    # Обработка результатов детекции
    if results_detect[0].masks is not None and len(results_detect[0].masks.xy) > 0:
        masks = results_detect[0].masks
        segments = masks.xy
        classes = results_detect[0].boxes.cls.cpu().numpy().astype(int)
        names = results_detect[0].names
        print(names)

        y_max_global = float('-inf')
        y_min_global = float('inf')
        distance_all = []
        coordinates = []
        not_normal = False
        contour_color = None
        object_info = {}

        for segment, clss in zip(segments, classes):
            if len(segment) > 0:

                segment = segment.astype(int)
                # Рисуем контур сегмента
                if not names[clss] == "flatness":
                    contour_color = color
                    cv2.polylines(frame, [segment], isClosed=True, color=contour_color, thickness=2)
                area = cv2.contourArea(segment)

                # Создаем бинарную маску для сегмента
                mask = numpy.zeros(frame.shape[:2], dtype=numpy.uint8)
                cv2.drawContours(mask, [segment], -1, 255, thickness=cv2.FILLED)

                # Вычисляем среднее значение пикселей внутри маски
                mean_pixel_value = cv2.mean(frame, mask=mask)[:3]  # Берем только BGR (первые 3 канала)

                distance = None
                moment = cv2.moments(segment)
                if names[clss] == "flatness":
                    distance, coordinate = contour_edge_distances(segment, frame)
                    coordinates.append(coordinate)
                    distance_all.append(distance)

                text_placement(moment, draw_area, area, frame)

                object_info = {
                    "class_name": names[clss],
                    "distance": None,
                    "segment": segment.tolist(),
                    "area": cv2.contourArea(segment),
                    "color": contour_color,
                    "mean_pixel_value": mean_pixel_value  # Среднее значение пикселей
                }
                print(object_info['distance'])
                object_data.append(object_info)

            if len(distance_all) > 0:
                if max(distance_all) > 24 or min(distance_all) < 13:
                    not_normal=True
                elif abs(max(distance_all)-min(distance_all))>=6:
                    not_normal = True
                if not_normal:

                    # try: cv2.polylines(frame, [segments], isClosed=True, color=color, thickness=2)
                    for i in range(len(distance_all)):
                        obj_info = object_data[i]
                        obj_info['color'] = color
                        object_data[i] = obj_info

                        x_mid,y_min,y_mid = coordinates[i]
                        cv2.line(frame, (x_mid, y_min), (x_mid, y_mid), (255, 0, 0), 1, cv2.LINE_AA)
                        cv2.putText(frame, f"H:{distance_all[i]}", (x_mid + 5, (y_min + y_mid) // 2),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

                    # except Exception as ex:
                    #     print(ex,'  ',range(len(distance_all)),'   ',distance_all )



    # Кодируем изображение в JPEG
    encode_status, buffer = cv2.imencode('.jpg', frame)
    if not encode_status:
        print('Не удалось закодировать изображение')
        return None, object_data if object_data else []
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    with locker:
        print(f'{color} - {object_data}')
    """if object_data:
        print("Обнаруженные объекты:")

        for i, obj in enumerate(object_data):
            if i == len(object_data) - 1:
                print(f"{obj['class_name']} \n", "console")
            else:
                print(f"{obj['class_name']}", "console") #text_placement"""

    # except Exception as ex:
    #     print(f'Ошибка распознавания модели {ex}')
    #     encoded_image = None

    return encoded_image, object_data
