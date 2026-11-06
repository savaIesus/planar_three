import cv2

from project.station.camera.validation import get_available_camera_indices_no_limit

class CamerasList:
    """
        Класс-хранилище для всех индексов подключённых камерер
        обновляет данные при вызове connect_to_cameras
    """
    cams_list = []

def connect_to_cameras():
    """
        Подключается ко всем доступным камерам, используя OpenCV (cv2).
        Определяет индексы доступных камер с помощью get_available_camera_indices().

        Returns:
            list[cv2.VideoCapture]: Список объектов VideoCapture для каждой подключенной камеры.
                                     Возвращает пустой список, если ни одна камера не была открыта.
        """
    Cam = CamerasList
    Cam.cams_list.clear()
    available_camera_indices = get_available_camera_indices_no_limit()

    camera_captures = []
    for index in available_camera_indices:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            camera_captures.append(cap)
            Cam.cams_list.append(index)
            print(f"Успешно подключились к камере с индексом {index}")

        else:
            print(f"Не удалось подключиться к камере с индексом {index}")

    print(Cam.cams_list)
    return camera_captures

