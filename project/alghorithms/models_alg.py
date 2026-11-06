import cv2
import numpy


from project.station.math import contour_edge_distances, text_placement


def result_of_detect(results_detect):

    masks = results_detect[0].masks
    segments = masks.xy
    classes = results_detect[0].boxes.cls.cpu().numpy().astype(int)
    names = results_detect[0].names
    print(names)

    return segments, classes, names


def default_models(segments, classes, names, frame, color, draw_area):

    object_info = {}
    object_data = []

    for segment, clss in zip(segments, classes):
        if len(segment) > 0:

            segment = segment.astype(int)
            # Рисуем контур сегмента
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
            text_placement(moment, draw_area, area, frame)

            object_info = {
                "class_name": names[clss],
                "distance": None,
                "segment": segment.tolist(),
                "area": cv2.contourArea(segment),
                "color": contour_color,
                "mean_pixel_value": mean_pixel_value  # Среднее значение пикселей
            }
            object_data.append(object_info)
            print(object_info['distance'])

    return object_data

def flatness_model(segments, classes, names, frame, color, draw_area, heights):

    distance_all = []
    coordinates = []
    not_normal = False
    contour_color = color
    object_data = []
    segments_list = []

    for segment, clss in zip(segments, classes):
        if len(segment) > 0:

            segments_list.append(segment)
            segment = segment.astype(int)
            area = cv2.contourArea(segment)

            # Создаем бинарную маску для сегмента
            mask = numpy.zeros(frame.shape[:2], dtype=numpy.uint8)
            cv2.drawContours(mask, [segment], -1, 255, thickness=cv2.FILLED)

            # Вычисляем среднее значение пикселей внутри маски
            mean_pixel_value = cv2.mean(frame, mask=mask)[:3]  # Берем только BGR (первые 3 канала)


            moment = cv2.moments(segment)

            distance, coordinate = contour_edge_distances(segment, frame)
            coordinates.append(coordinate)
            distance_all.append(distance)

            text_placement(moment, draw_area, area, frame)

            object_info = {
                "class_name": names[clss],
                "distance": distance,
                "segment": segment.tolist(),
                "area": cv2.contourArea(segment),
                "color": None,
                "mean_pixel_value": mean_pixel_value  # Среднее значение пикселей
            }
            # print(object_info['distance'])
            object_data.append(object_info)

    # print(heights["min"],heights["max"],heights["avg"])
    if max(distance_all) >= heights["max"] or min(distance_all) <= heights["min"]: # > 24 < 13 было (стекло понизил с 0.65, сварка с 0.25)
        not_normal = True

    elif abs(max(distance_all) - min(distance_all)) >= heights["avg"]:
        not_normal = True

    # try: cv2.polylines(frame, [segments], isClosed=True, color=color, thickness=2)
    if not_normal:
        for i in range(len(distance_all)):
            obj_info = object_data[i]
            obj_info['color'] = contour_color
            object_data[i] = obj_info

            x_mid, y_min, y_mid = coordinates[i]

            for segment in segments_list:
                if len(segment) > 0:
                    segment = segment.astype(int)
                    cv2.polylines(frame, [segment], isClosed=True, color=contour_color, thickness=2)

            cv2.line(frame, (x_mid, y_min), (x_mid, y_mid), (255, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, f"H:{distance_all[i]}", (x_mid + 5, (y_min + y_mid) // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0 ), 1, cv2.LINE_AA)

    else:
        for i in range(len(distance_all)):
            for segment in segments_list:
                if len(segment) > 0:
                    segment = segment.astype(int)
                    cv2.polylines(frame, [segment], isClosed=True, color=contour_color, thickness=2)

    return object_data




