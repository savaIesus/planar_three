import base64, os
import threading

from flet import *
import cv2

from project.configuration.worker import write_to_json
from project.application.addition.colors import color_mode
from project.application.addition.error_message import show_error
from project.application.addition.load_gif_path import get_path
from project.station.camera.frame_settings import apply_settings_to_frame
from project.station.camera.connection import CamerasList
# Глобальный параметр, отображающий, подключена ли камера к элементам вкладки
BUTTON_CLICKED = 0
application_colors = color_mode()



class CameraContainer(Container):
    def __init__(self):
        self.image = Image(
            src=get_path(),
            fit="fill",
            width=600,
            height=600,
        )
        super().__init__(
            content=self.image,
            width=600,
            height=600,
            bgcolor=application_colors["background"],
            border_radius=10,
            alignment=alignment.center,
        )


def create_camera_mechanical_layer():
    """
    Функция, создающая вкладку механической калибровки положения камеры и
    подключающая все контролы, содержащиеся в ней, к обработчикам и событиям.

    :return: flet.Tab camera_mechanical_tab
    """
    thr_m, thr_r, thr_l = None, None,None
    def camera_connect(_e, cam, window):
        """
        Вспомогательная функция-обработчик нажатия на кнопку "Подключить камеру"
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        global BUTTON_CLICKED
        caps = []
        try:
            cap = cv2.VideoCapture(cam)
            BUTTON_CLICKED = 1
            while True:
                # Чтение изображения с подключенной камеры,
                # конвертация его в Base64 и трансляция в окно
                ret, frame = cap.read()
                frame = apply_settings_to_frame(frame)
                _, buffer = cv2.imencode('.jpg', frame)
                img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                if BUTTON_CLICKED == 1:
                    window.content.src_base64 = img_base64
                    window.update()
                else:
                    cap.release()
                    break

        except Exception:
            show_error("Ошибка подключения!",
                       "Ошибка OpenCV: камера не обнаружена, перезапустите программу",
                       _e.page)

    def on_click_camera_connect(_e):
        nonlocal thr_r, thr_l, thr_m
        write_to_json('project/station/statuses.json', 'update_frame', 1)

        try:
            thr_m = threading.Thread(target=camera_connect, args=(_e, CamerasList.cams_list[0], camera_image_mid),
                                     daemon=True)
            thr_r = threading.Thread(target=camera_connect, args=(_e, CamerasList.cams_list[1], camera_image_right),
                                     daemon=True)
            thr_l = threading.Thread(target=camera_connect, args=(_e, CamerasList.cams_list[2], camera_image_left),
                                     daemon=True)
            thr_m.start()
            thr_l.start()
            thr_r.start()
        except Exception as ex:
            print(f'Не удалось вывести камеру: {ex}')

    def on_click_camera_disconnect(_e):
        """
        Вспомогательная функция-обработчик нажатия на кнопку "Отключить камеру"
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        nonlocal thr_r, thr_l, thr_m
        global BUTTON_CLICKED

        BUTTON_CLICKED = 0
        for window in [camera_image_left,camera_image_mid,camera_image_right]:
            window.content.src_base64 = ""
            window.update()
        for thr in [thr_l,thr_m,thr_r]:
            thr.join()
            thr.join()
            thr.join()

    def on_click_load_image(_e):
        """
        Вспомогательная функция-обработчик нажатия на кнопку "Загрузить изображение".
        Загружает в окно изображение по фиксированному пути.

        :param _e: Событие нажатия на кнопку
        :return: None
        """
        nonlocal reference_image
        reference_image.content.controls[0].src = "project/configuration/reference.png"

        _e.page.update()

    def on_click_unload_image(_e):
        """
        Вспомогательная функция-обработчик нажатия на кнопку "Удалить изображение".
        Удаляет из окна изображение и возвращает ему стандартное содержание.

        :param _e: Событие нажатия на кнопку
        :return: None
        """
        nonlocal reference_image
        reference_image.content.controls[0].src = get_path()

        _e.page.update()

    # Элементы левого подмакета - контейнер для изображения с камеры и управляющие кнопки
    camera_title = Text("Изображение с камеры",
                        size=18,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"])


    camera_image_right = CameraContainer()
    camera_image_mid = CameraContainer()
    camera_image_left = CameraContainer()

    camera_connect_btn = ElevatedButton(
                text="Подключить камеру",
                width=250,
                height=48,
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=10),
                    overlay_color=application_colors["hover"],
                    bgcolor=application_colors["inactive"],
                    color=application_colors["text"],
                    text_style=TextStyle(size=18, weight=FontWeight.BOLD),
                    animation_duration=300,
                ),
                on_click=on_click_camera_connect
            )

    camera_disconnect_btn = ElevatedButton(
                text="Отключить камеру",
                width=250,
                height=48,
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=10),
                    overlay_color=application_colors["hover"],
                    bgcolor=application_colors["inactive"],
                    color=application_colors["text"],
                    text_style=TextStyle(size=18, weight=FontWeight.BOLD),
                    animation_duration=300,
                ),
                on_click=on_click_camera_disconnect
            )

    camera_buttons_row = Row(
        [camera_connect_btn, camera_disconnect_btn],
        spacing=20
    )

    # Элементы правого подмакета - контейнер для изображения-эталона и управляющие кнопки
    reference_title = Text("Эталонное изображение",
                           size=18,
                           weight=FontWeight.BOLD,
                           color=application_colors["text"])

    reference_image = Container(
        content=Stack(
            controls=[
                Image(
                    src=get_path(),
                    fit=ImageFit.FILL,
                    width=700,
                    height=700,
                )
            ]
        ),
        width=700,
        height=700,
        bgcolor=application_colors["background"],
        border_radius=10,
        alignment=alignment.center,
    )

    reference_load_btn = ElevatedButton(
                text="Загрузить",
                width=250,
                height=48,
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=10),
                    overlay_color=application_colors["hover"],
                    bgcolor=application_colors["inactive"],
                    color=application_colors["text"],
                    text_style=TextStyle(size=18, weight=FontWeight.BOLD),
                    animation_duration=300,
                ),
                on_click=on_click_load_image
            )

    reference_delete_btn = ElevatedButton(
                text="Удалить",
                width=250,
                height=48,
                style=ButtonStyle(
                    shape=RoundedRectangleBorder(radius=10),
                    overlay_color=application_colors["hover"],
                    bgcolor=application_colors["inactive"],
                    color=application_colors["text"],
                    text_style=TextStyle(size=18, weight=FontWeight.BOLD),
                    animation_duration=300,
                ),
        on_click=on_click_unload_image
            )

    reference_buttons_row = Row(
        [reference_load_btn, reference_delete_btn],
        spacing=20
    )

    left_column = Column(
        [
            camera_title,
            Container(height=12),
            Row([camera_image_left,camera_image_mid,camera_image_right]),
            Container(height=8),
            camera_buttons_row
        ],
        spacing=10,
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    right_column = Column(
        [
            reference_title,
            Container(height=12),
            reference_image,
            Container(height=8),
            reference_buttons_row
        ],
        spacing=10,
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    main_row = Row(
        controls=[
            Container(expand=True),
            left_column,
            Container(expand=True),
            # right_column,
            # Container(expand=True)
        ],
        spacing=20,
    )

    camera_mechanical_tab = Tab(
        text="Механическая настройка камеры",
        content=Container(
            content=Column(
                controls=[
                    main_row
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            ),
            padding=20,
            bgcolor=application_colors["background"],
        ),
    )

    return camera_mechanical_tab
