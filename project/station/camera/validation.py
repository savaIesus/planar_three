import cv2


def get_available_camera_indices():
    """
    Проверяет доступные камеры и возвращает список их индексов.

    Использует OpenCV (cv2). Пробует открыть камеры, увеличивая индекс,
    пока не встретит 10 последовательно недоступных камер. Это позволяет
    обнаружить все доступные камеры, даже если между ними есть "пробелы"
    в индексах.

    Returns:
        list[int]: Список индексов доступных камер. Пустой список, если камер нет.
    """


    camera_index = 0
    consecutive_failures = 0       # Счетчик последовательных неудач
    available_camera_indices = []
    max_consecutive_failures = 10  # Максимальное количество последовательных неудач

    while consecutive_failures < max_consecutive_failures:
        cap = cv2.VideoCapture(camera_index)
        if  cap.isOpened():
            available_camera_indices.append(camera_index)
            cap.release()
            consecutive_failures = 0   # Сбрасываем счётчик при успехе
        else:
            consecutive_failures += 1  # Увеличиваем счетчик при неудаче

        camera_index += 1


    return available_camera_indices


def get_available_camera_indices_no_limit():
    """
    Проверяет доступные камеры и возвращает список их индексов.

    Использует OpenCV (cv2).  Пробует открыть камеры с увеличивающимися индексами,
    пока не произойдет ошибка, которую cv2.VideoCapture *не сможет обработать*.

    Этот метод *потенциально* может вызвать проблемы, если система
    будет бесконечно "притворяться", что камеры есть.  Используйте с осторожностью
    и *только если* метод get_available_camera_indices с ограничением не работает.
    Обычно лучше использовать get_available_camera_indices.

    Returns:
        list[int]: Список индексов доступных камер.  Пустой список, если камер нет.
    """
    camera_index = 0
    available_camera_indices = []

    while True:
        try:
            cap = cv2.VideoCapture(camera_index)
            if cap is None or not cap.isOpened():
                break
            available_camera_indices.append(camera_index)
            cap.release()
            camera_index += 1
        except Exception as e:
            print(f"Ошибка при попытке открыть камеру с индексом {camera_index}: {e}")
            break

    return available_camera_indices
