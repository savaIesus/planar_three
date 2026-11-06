import time
import base64
from json import JSONDecodeError
import threading
import cv2, os


from types import SimpleNamespace
from project.alghorithms.contour import draw_contour
from project.alghorithms.network import locker
from project.station.camera.connection import connect_to_cameras
from project.configuration.worker import read_from_json, write_to_json
from project.alghorithms.tolerance_calculation import  cell_color_change #process_distances
from project.station.camera.frame_settings import apply_settings_to_frame
import project.station.weights.networks_vault as nv

write_to_json("project/station/statuses.json", "paused", 0)
write_to_json("project/station/statuses.json", "stopped", 0)

def update_camera_feed(left_image, right_image, snake_buttons):
    """
    Запускает поток обновления изображения в контейнере Flet.

    Args:
        left_image (ft.Image): Объект изображения, который нужно обновлять.
        right_image (ft.Image): Дополнительный объект изображения,
                                который обновляется только при смене состояния.
    :param right_image:
    :param left_image:
    :param snake_buttons:
    """
    cameras = connect_to_cameras()
    current_camera = -1


    if not cameras:
        print("Камеры не найдены.")
        return

    def capture_frame(camera):
        """
        Читает кадр с камеры и конвертирует его в base64 для отображения в Flet.

        Args:
            camera (cv2.VideoCapture): Объект видеопотока камеры.

        Returns:
            str: Base64-кодированное изображение или None, если не удалось получить кадр.
        """
        success, frame = camera.read()
        if success:
            frame = apply_settings_to_frame(frame)
            _, buffer = cv2.imencode(".jpg", frame)
            encoded_image = base64.b64encode(buffer.tobytes()).decode('utf-8')
            return encoded_image
        return None

    print_lock = threading.Lock()
    right_img = [None, None, None]
    obj_data = [[],[],[]]
    cameras_threads = []
    def clear_data():
        nonlocal  obj_data, cameras_threads
        obj_data = [[] for _ in obj_data]
        cameras_threads.clear()
        return None

    def start_processing(cam_id, Cameras_List):
        """
        функция для начала обработки и созданя изображений

        :param cam_id: - номер обрабатываемой камеры
        :param Cameras_List: - поток камеры
        :return: None
        """
        nonlocal right_img, obj_data
        with print_lock:
            t = time.time()
            print(f'Старт потока - [{threading.current_thread().name}]{t: .2f} - камера {cam_id}')
        frame = capture_frame(Cameras_List[cam_id])
        right_img[cam_id], obj_data[cam_id] = draw_contour(frame, cam_id,nv.models)
        with print_lock:
            print(f'[{threading.current_thread().name}]{t - time.time() : .2f} - камера {cam_id}')

    def update_loop():
        def process_all_cameras(cameras_list):
            nonlocal current_camera, cameras, obj_data
            obj_data = [[], [], []]
            if read_from_json("project/station/statuses.json", "stopped") == 0:
                time.sleep(0.4)
                cam_update_status = read_from_json('project/station/statuses.json', 'update_frame')
                if (not any(cameras_list[i].isOpened() for i in [0,1,2])) or cam_update_status == 1 :
                    cameras = connect_to_cameras()
                    cameras_list=cameras
                    current_camera = -1
                    write_to_json('project/station/statuses.json', 'update_frame', 0)

                frame_center = capture_frame(cameras_list[0])
                frame_down = capture_frame(cameras_list[1])
                frame_up = capture_frame(cameras_list[2])

                if frame_center and frame_down and frame_up:
                    if read_from_json("project/station/statuses.json",
                                      "right_view_waiting") == 1:
                        clear_data()
                        for cam in [0, 1, 2]:
                            cameras_thread = threading.Thread(target=start_processing, args=(cam, cameras_list))
                            cameras_thread.start()
                            cameras_threads.append(cameras_thread)
                        for thr in cameras_threads:
                            thr.join()
                        cameras_threads.clear()

                        while read_from_json("project/station/statuses.json",
                                      "start_showing") != 1:
                            time.sleep(0.1)
                        while read_from_json("project/station/statuses.json", "paused") != 0:
                            time.sleep(0.1)

                        for cam in [0, 1, 2]:
                            print(obj_data[cam])
                            print_lock.acquire()
                            cell_color_change(obj_data[cam], snake_buttons)
                            left_image.src_base64 = capture_frame(cameras_list[cam])
                            left_image.update()
                            current_camera = cam
                            right_image.src_base64 = right_img[cam]
                            right_image.update()
                            time.sleep(0.8)
                            print_lock.release()
                        write_to_json("project/station/statuses.json",
                                      "start_showing", 0)

                          # модифициовать для нормальной покраски ячейки
                        write_to_json("project/station/statuses.json",
                                      "right_view_waiting", 0)



                else:
                    left_image.src_base64 = ""
                    left_image.update()
                    right_image.src_base64 = ""
                    right_image.update()
                    for cams in cameras_list:
                        cams.release()

                    write_to_json("project/station/statuses.json",
                                  "start_showing", 0)
                    write_to_json("project/station/statuses.json",
                                  "right_view_waiting", 0)

        while True:
            try:
                move_to_home = read_from_json(
                        "project/station/statuses.json",
                        "moved_to_home") == 1

                move_to_cell = read_from_json(
                        "project/station/statuses.json",
                        "moved_to_cell") == 1
                if move_to_home or move_to_cell:
                    process_all_cameras(cameras)
            except JSONDecodeError:
                print("ОШИБКА update loop")
                continue

    write_to_json("project/station/statuses.json",
                  "moved_to_home",
                  0)
    thread = threading.Thread(target=update_loop, args = [], daemon=True)
    thread.start()

    def display_selected_camera(cameras_list):
        nonlocal current_camera
        while True:
            try:

                if all(items is not None for items in right_img):
                    status = read_from_json("project/station/statuses.json","change_capture")

                    if status == 2:    # Вперёд
                        current_camera = (current_camera + 1) % 3
                    elif status == 1:  # Назад
                        current_camera = (current_camera - 1) % 3
                    if status in [1, 2]:

                        left_image.src_base64 = capture_frame(cameras_list[current_camera])
                        left_image.update()

                        right_image.src_base64 = right_img[current_camera]
                        right_image.update()

                        write_to_json("project/station/statuses.json", "change_capture", -1)
            except Exception as ex:
                print(f'Ошибка переключения камер! - {ex}')
            time.sleep(0.5)
    display_change_thread = threading.Thread(target=display_selected_camera, args=[cameras],daemon=True)
    display_change_thread.start()




