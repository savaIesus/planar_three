import base64
import cv2
from flet import *

from project.application.addition.colors import color_mode
from project.application.addition.error_message import show_error
from project.application.addition.load_gif_path import get_path
from project.application.addition.object import set_object_state
from project.application.addition.password_message import show_password_message
from project.station.camera.frame_settings import apply_settings_to_frame
from project.station.requests import move_to_coordinates, move_to_home
from project.configuration.worker import write_to_json, read_from_json
from project.station.connection import establish_connection, close_connection

# Глобальный флаг, отражает, подключена ли во вкладке камера
BUTTON_CLICKED = 0
dimensions = []

def get_current_position():
    global dimensions

    dimensions.append(
        read_from_json(
            r'project\configuration\coordinates.json',
            'current_coordinate_of_the_station_by_x'
        )
    )
    dimensions.append(
        read_from_json(
            r'project\configuration\coordinates.json',
            'current_coordinate_of_the_station_by_y'
        )
    )
    dimensions.append(
        read_from_json(
            r'project\configuration\coordinates.json',
            'current_coordinate_of_the_station_by_z'
        )
    )
    for ind in range(len(dimensions)):
        if dimensions[ind] < 0:
            dimensions[ind] = 0
        elif dimensions[ind] > 300:
            dimensions[ind] = 300


def create_calibration_layer():
    """
    Функция-конструктор вкладки "Калибровка первой ячейки".
    :return: flet.Tab calibration_tab
    """
    get_current_position()

    application_colors = color_mode()
    step_buttons = []
    button_titles = [" ", "↑", " ", "↑", "⌂ ВСЕ", "←", "⌂", "→",
                     "⌂", "⌂ X", " ", "↓", " ", "↓", "⌂ Y"]
    tooltips = [
        "",
        "Движение камеры вперёд вдоль палеты на заданную величину шага в мм",
        "",
        "Движение камеры от палеты на заданную величину шага в мм",
        "Движение камеры на нулевые координаты по всем осям",
        "Движение камеры влево вдоль палеты на заданную величину шага в мм",
        "Движение камеры на нулевые координаты в плоскости палеты",
        "Движение камеры вправо вдоль палеты на заданную величину шага в мм",
        "Движение камеры на нулевые координаты по высоте",
        "Движение камеры на нулевые координаты по горизонтали вдоль палеты",
        "",
        "Движение камеры назад вдоль палеты на заданную величину шага в мм",
        "",
        "Движение камеры к палете на заданную величину шага в мм",
        "Движение камеры на нулевые координаты по вертикали вдоль палеты",
    ]

    def on_click_camera_connect(_e):
        """
        Функция-обработчик нажатия на кнопку "Подключить камеру".
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        global BUTTON_CLICKED
        write_to_json('project/station/statuses.json', 'update_frame', 1)

        try:
            cap = cv2.VideoCapture(0)
            BUTTON_CLICKED = 1
            while True:
                # Захват изображения с подключенной камеры,
                # его кодирование в Base64 и трансляция в левом окне
                ret, frame = cap.read()
                frame = apply_settings_to_frame(frame)
                _, buffer = cv2.imencode('.jpg', frame)
                img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                if BUTTON_CLICKED == 1:
                    left_image_container.content.src_base64 = img_base64
                    left_image_container.update()
                else:
                    cap.release()
                    break

        except Exception:
            show_error("Ошибка подключения!",
                       "Ошибка OpenCV: камера не обнаружена, перезапустите программу",
                       _e.page)

    def on_click_camera_disconnect(_e):
        """
        Функция-обработчик нажатия на кнопку "Отключить камеру".
        :param _e: Событие нажатия на кнопку.
        :return: None
        """
        global BUTTON_CLICKED

        BUTTON_CLICKED = 0
        left_image_container.content.src_base64 = ""
        left_image_container.update()

    def make_styles(bgcolor, color):
        """
        Вспомогательная функция-генератор стилей для различных кнопок вкладки
        :param bgcolor: Цвет подложки кнопок
        :param color: Цвет текста кнопок
        :return: List[ButtonStyle] - список сгенерированных стилей для кнопок
        """
        return [
            ButtonStyle(
                shape=RoundedRectangleBorder(radius=radius),
                overlay_color=application_colors["hover"],
                bgcolor=bgcolor,
                color=color,
                text_style=TextStyle(size=18, weight=FontWeight.BOLD),
                animation_duration=300,
            )
            for radius in [
                border_radius.only(12, 0, 12, 0),
                0,
                border_radius.only(0, 12, 0, 12)
            ]
        ]

    # Генерация стилей для повторяющихся кнопок
    step_styles_inactive = make_styles(application_colors["inactive"],
                                       application_colors["text"])
    step_styles_inactive_disabled = make_styles(application_colors["top_bar"],
                                                application_colors["unclickable"])
    step_styles_active = make_styles(application_colors["active"],
                                     application_colors["text"])
    step_styles_active_disabled = make_styles(application_colors["active_unclickable"],
                                              application_colors["unclickable"])

    left_image_container = Container(
        content=Image(src=get_path(), fit=ImageFit.FILL, width=720, height=720),
        width=720,
        height=720,
        bgcolor=application_colors["background"],
        border_radius=12,
        alignment=alignment.center,
    )

    # Стандартные стили для кнопок, не нуждающиеся в генераторах
    default_active_button_style = ButtonStyle(
        shape=RoundedRectangleBorder(radius=10),
        overlay_color=application_colors["hover"],
        bgcolor=application_colors["inactive"],
        color=application_colors["text"],
        text_style=TextStyle(size=18, weight=FontWeight.BOLD),
        animation_duration=300,
    )

    default_inactive_button_style = ButtonStyle(
        shape=RoundedRectangleBorder(radius=10),
        overlay_color=application_colors["hover"],
        bgcolor=application_colors["top_bar"],
        color=application_colors["unclickable"],
        text_style=TextStyle(size=18, weight=FontWeight.BOLD),
        animation_duration=300,
    )

    new_buttons = Row(
        controls=[
            ElevatedButton(
                text="Подключить камеру",
                width=250,
                height=48,
                style=default_active_button_style,
                on_click=on_click_camera_connect
            ),
            ElevatedButton(
                text="Отключить камеру",
                width=250,
                height=48,
                style=default_active_button_style,
                on_click=on_click_camera_disconnect
            ),
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=20,
    )

    left_side = Column(
        controls=[
            Text("Изображение с камеры",
                 size=18,
                 weight=FontWeight.BOLD,
                 color=application_colors["text"]),
            Container(height=12),
            left_image_container,
            Container(height=10),
            new_buttons,
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    def axes_update():
        nonlocal x_axis, y_axis, z_axis

        x_axis.controls[0].controls[1].controls[0].value = read_from_json(
            "project/configuration/coordinates.json",
            "current_coordinate_of_the_station_by_x")
        y_axis.controls[0].controls[1].controls[0].value = read_from_json(
            "project/configuration/coordinates.json",
            "current_coordinate_of_the_station_by_y")
        z_axis.controls[0].controls[1].controls[0].value = read_from_json(
            "project/configuration/coordinates.json",
            "current_coordinate_of_the_station_by_z")

        x_axis.update()
        y_axis.update()
        z_axis.update()

    def on_click_up_xy(_e):
        """
        Движения робота вверх по оси Y.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")

            move_to_coordinates(
                connection,
                x,
                y + read_from_json(
                    "project/configuration/coordinates.json",
                    "movement_step"),
                z)

            close_connection(connection)

        axes_update()

    def on_click_left_xy(_e):
        """
        Движение робота влево (назад) по оси X.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")

            step = read_from_json(
                "project/configuration/coordinates.json",
                "movement_step")
            if x - step >= 0:
                move_to_coordinates(
                    connection,
                    x - step,
                    y,
                    z)
            else:
                pass

        axes_update()

    def on_click_home_xy(_e):
        """
        Движение робота на домашние координаты по осям X и Y (сейчас - по всем).
        :param _e: Событие нажатия на кнопку
        :return: None
        """

        connection = establish_connection(_e.page)

        if connection is not None:
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")

            move_to_coordinates(connection,0,0, z)
            close_connection(connection)

        axes_update()

    def on_click_right_xy(_e):
        """
        Движение робота вправо (вперёд) по оси X.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")

            move_to_coordinates(
                connection,
                x + read_from_json(
                    "project/configuration/coordinates.json",
                    "movement_step"),
                y,
                z)

            close_connection(connection)

        axes_update()

    def on_click_down_xy(_e):
        """
        Движение робота вниз по оси Y.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")
            step = read_from_json(
                    "project/configuration/coordinates.json",
                    "movement_step")
            if y - step >= 0:
                move_to_coordinates(
                    connection,
                    x,
                    y- step,
                    z)
            else:
                pass

            close_connection(connection)

        axes_update()

    def on_click_up_z(_e):
        """
        Движение робота вверх по оси Z.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")
            step = read_from_json(
                    "project/configuration/coordinates.json",
                    "movement_step")
            if z + step >= 0:
                move_to_coordinates(
                    connection,
                    x,
                    y,
                    z + step)
            else:
                pass

            close_connection(connection)

        axes_update()

    def on_click_home_z(_e):
        """
        Возврат робота на домашние координаты по оси Z. (сейчас - по всем)
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")

            move_to_coordinates(connection, x, y,0)
            close_connection(connection)

        axes_update()

    def on_click_down_z(_e):
        """
        Движение робота вниз по оси Z.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")

            step = read_from_json(
                "project/configuration/coordinates.json",
                "movement_step")
            if z - step >= 0:
                move_to_coordinates(
                    connection,
                    x,
                    y,
                    z - step)
            else:
                pass

        axes_update()

    def on_click_home_all(_e):
        """
        Возвращение робота на домашние координаты по всем осям.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            move_to_home(connection)
            close_connection(connection)

        axes_update()

    def on_click_home_x(_e):
        """
        Возвращение робота на домашние координаты по оси X. (сейчас - по всем)
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        connection = establish_connection(_e.page)

        if connection is not None:
            y = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_y")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")

            move_to_coordinates(connection,0, y, z)
            close_connection(connection)

        axes_update()

    def on_click_home_y(_e):
        """
        Возвращение робота на домашние координаты по оси Y. (сейчас - по всем)
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        print("Нажата кнопка возврата домой по Y.")
        connection = establish_connection(_e.page)

        if connection is not None:
            x = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_x")
            z = read_from_json(
                "project/configuration/coordinates.json",
                "current_coordinate_of_the_station_by_z")

            move_to_coordinates(connection, x, 0, z)
            close_connection(connection)

        axes_update()

    def step_changed(_e, value):
        """
        Функция-обработчик нажатия на кнопку смены шага движения робота при калибровке.
        :param _e: Событие нажатия на кнопку
        :param value: Выбранное значение шага
        :return: None
        """
        nonlocal step_buttons
        step_buttons[0].style = step_styles_inactive[0]
        step_buttons[1].style = step_styles_inactive[1]
        step_buttons[2].style = step_styles_inactive[1]
        step_buttons[3].style = step_styles_inactive[2]

        if value == 0.01:
            step_buttons[0].style = step_styles_active[0]
            write_to_json(
                "project/configuration/coordinates.json",
                "movement_step",
                0.01)
        elif value == 0.1:
            step_buttons[1].style = step_styles_active[1]
            write_to_json(
                "project/configuration/coordinates.json",
                "movement_step",
                0.1)
        elif value == 1:
            step_buttons[2].style = step_styles_active[1]
            write_to_json(
                "project/configuration/coordinates.json",
                "movement_step",
                1)
        elif value == 10:
            step_buttons[3].style = step_styles_active[2]
            write_to_json(
                "project/configuration/coordinates.json",
                "movement_step",
                10)

        _e.page.update()

    async def change_coordinates(_e):
        """
        Обработчик нажатия на кнопку входа в режим изменения координат.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        pword_ok = await show_password_message(_e)

        if pword_ok:
            # Активация управляющих кнопок
            lower_buttons.controls[0].bgcolor = application_colors["top_bar"]
            lower_buttons.controls[0].color = application_colors["unclickable"]
            set_object_state(lower_buttons.controls[0], True)

            lower_buttons.controls[1].bgcolor = application_colors["inactive"]
            lower_buttons.controls[1].color = application_colors["text"]
            set_object_state(lower_buttons.controls[1], False)

            for step_button in step_buttons:
                if step_button.style in step_styles_inactive_disabled:
                    if step_button.style == step_styles_inactive_disabled[0]:
                        step_button.style = step_styles_inactive[0]
                    elif step_button.style == step_styles_inactive_disabled[1]:
                        step_button.style = step_styles_inactive[1]
                    elif step_button.style == step_styles_inactive_disabled[2]:
                        step_button.style = step_styles_inactive[2]

                elif step_button.style in step_styles_active_disabled:
                    if step_button.style == step_styles_active_disabled[0]:
                        step_button.style = step_styles_active[0]
                    elif step_button.style == step_styles_active_disabled[1]:
                        step_button.style = step_styles_active[1]
                    elif step_button.style == step_styles_active_disabled[2]:
                        step_button.style = step_styles_active[2]

                set_object_state(step_button, False)

            for i in range(3):
                for j in range(5):
                    button_grid.controls[i].controls[j].bgcolor = application_colors["inactive"]
                    button_grid.controls[i].controls[j].color = application_colors["text"]
                    set_object_state(button_grid.controls[i].controls[j], False)

        await _e.page.update_async()

    def save_coordinates(_e):
        """
        Функция-обработчик нажатия на кнопку "Сохранить координаты"
        (выхода из режима изменения координат).
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        nonlocal x_axis, y_axis, z_axis
        write_to_json(
            "project/configuration/coordinates.json",
            "x_coordinate_of_the_first_cell",
            round(
                read_from_json(
                    "project/configuration/coordinates.json",
                    "current_coordinate_of_the_station_by_x"),
                3))
        write_to_json(
            "project/configuration/coordinates.json",
            "y_coordinate_of_the_first_cell",
            round(
                read_from_json(
                    "project/configuration/coordinates.json",
                    "current_coordinate_of_the_station_by_y"),
                3))
        write_to_json(
            "project/configuration/coordinates.json",
            "z_coordinate_of_the_first_cell",
            round(
                read_from_json(
                    "project/configuration/coordinates.json",
                    "current_coordinate_of_the_station_by_z"),
                3))

        # Деактивация управляющих кнопок
        lower_buttons.controls[0].bgcolor = application_colors["inactive"]
        lower_buttons.controls[0].color = application_colors["text"]
        set_object_state(lower_buttons.controls[0], False)

        lower_buttons.controls[1].bgcolor = application_colors["top_bar"]
        lower_buttons.controls[1].color = application_colors["unclickable"]
        set_object_state(lower_buttons.controls[1], True)

        for step_button in step_buttons:
            if step_button.style in step_styles_inactive:
                if step_button.style == step_styles_inactive[0]:
                    step_button.style = step_styles_inactive_disabled[0]
                elif step_button.style == step_styles_inactive[1]:
                    step_button.style = step_styles_inactive_disabled[1]
                elif step_button.style == step_styles_inactive[2]:
                    step_button.style = step_styles_inactive_disabled[2]

            elif step_button.style in step_styles_active:
                if step_button.style == step_styles_active[0]:
                    step_button.style = step_styles_active_disabled[0]
                elif step_button.style == step_styles_active[1]:
                    step_button.style = step_styles_active_disabled[1]
                elif step_button.style == step_styles_active[2]:
                    step_button.style = step_styles_active_disabled[2]

            set_object_state(step_button, True)

        for i in range(3):
            for j in range(5):
                button_grid.controls[i].controls[j].bgcolor = application_colors["top_bar"]
                button_grid.controls[i].controls[j].color = application_colors["unclickable"]
                set_object_state(button_grid.controls[i].controls[j], True)

        x_axis.update()
        y_axis.update()
        z_axis.update()

    # Сетка кнопок, управляющих движением робота во время калибровки
    button_grid = Column(
        controls=[
            Row(
                controls=[
                    ElevatedButton(
                        text=button_titles[i * 5 + j],
                        tooltip=tooltips[i * 5 + j],
                        width=110,
                        height=110,
                        style=ButtonStyle(
                            shape=RoundedRectangleBorder(radius=8),
                            overlay_color=application_colors["hover"],
                            bgcolor=application_colors["top_bar"],
                            color=application_colors["unclickable"],
                            text_style=TextStyle(
                                size=20,
                                weight=FontWeight.BOLD,
                                font_family="Montserrat"),
                            animation_duration=300,
                        ),
                        opacity=0 if button_titles[i * 5 + j] == " " else 1,
                        on_click=(
                            on_click_up_xy if button_titles[i * 5 + j] == "↑"
                                              and i == 0 and j == 1 else
                            on_click_up_z if button_titles[i * 5 + j] == "↑"
                                             and i == 0 and j == 3 else
                            on_click_home_all if button_titles[i * 5 + j] == "⌂ ВСЕ" else
                            on_click_left_xy if button_titles[i * 5 + j] == "←" else
                            on_click_home_xy if button_titles[i * 5 + j] == "⌂" and j == 1 else
                            on_click_right_xy if button_titles[i * 5 + j] == "→" else
                            on_click_home_z if button_titles[i * 5 + j] == "⌂" and j == 3 else
                            on_click_home_x if button_titles[i * 5 + j] == "⌂ X" else
                            on_click_down_xy if button_titles[i * 5 + j] == "↓" and j == 1 else
                            on_click_down_z if button_titles[i * 5 + j] == "↓" and j == 3 else
                            on_click_home_y if button_titles[i * 5 + j] == "⌂ Y" else None
                        ),
                        disabled=True,
                    )
                    for j in range(5)  # 3 кнопки в строке
                ],
                alignment=alignment.center
            )
            for i in range(3)  # 5 строк
        ],
        alignment=alignment.center
    )

    # Ряд кнопок, отвечающих за выбор значения шага
    step_block = Row(
        controls=[
            Text(value="Шаг: ", size=18, weight=FontWeight.BOLD, color=application_colors["text"]),
            Container(width=12),
            *(
                ElevatedButton(
                    text=t, width=104, height=40,
                    style=s[i], disabled=True,
                    on_click=lambda e, v=v: step_changed(e, v)
                ) for t, v, s, i in [
                ("0.01", 0.01, step_styles_active_disabled, 0),
                ("0.1", 0.1, step_styles_inactive_disabled, 1),
                ("1", 1, step_styles_inactive_disabled, 1),
                ("10", 10, step_styles_inactive_disabled, 2)
            ]
            )
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=2
    )

    for button in step_block.controls[2:]:
        step_buttons.append(button)

    # Диаграмма оси X
    x_axis = Column(
        controls=[
            Row(
                controls=[
                    Text(
                        value="X",
                        size=24,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Stack(
                        controls=[
                            Slider(
                                value=dimensions[0],
                                min=0,
                                max=300,
                                width=700,
                                disabled=True,
                                tooltip="По оси X осуществляется движение влево/вправо вдоль палеты"
                            ),
                            Container(
                                content=Column(
                                    controls=[
                                        Container(
                                            width=20,
                                            height=20,
                                            bgcolor=application_colors["text"],
                                            border_radius=border_radius.all(15),
                                        ),
                                        Text(
                                            value=str(read_from_json(
                                                "project/configuration/coordinates.json",
                                                "x_coordinate_of_the_first_cell")),
                                            color=application_colors["text"],
                                            size=16,
                                        )
                                    ],
                                    spacing=5
                                ),
                                offset=(read_from_json(
                                    "project/configuration/coordinates.json",
                                    "x_coordinate_of_the_first_cell") / 16, 0.3),
                            ),
                        ],
                        width=700,
                        height=50,
                    ),
                ],
                alignment=alignment.center
            ),
        ],
        alignment=alignment.center,
        spacing=5
    )

    # Диаграмма оси Y
    y_axis = Column(
        controls=[
            Row(
                controls=[
                    Text(
                        value="Y",
                        size=24,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Stack(
                        controls=[
                            Slider(
                                value=dimensions[1],
                                min=0,
                                max=300,
                                width=700,
                                disabled=True,
                                tooltip="По оси Y осуществляется движение вперёд/назад вдоль палеты"
                            ),
                            Container(
                                content=Column(
                                    controls=[
                                        Container(
                                            width=20,
                                            height=20,
                                            bgcolor=application_colors["text"],
                                            border_radius=border_radius.all(15),
                                        ),
                                        Text(
                                            value=str(
                                                read_from_json(
                                                    "project/configuration/coordinates.json",
                                                    "y_coordinate_of_the_first_cell")),
                                            color=application_colors["text"],
                                            size=16,
                                        )
                                    ],
                                    alignment=alignment.center,
                                    spacing=5
                                ),
                                offset=(read_from_json(
                                    "project/configuration/coordinates.json",
                                    "y_coordinate_of_the_first_cell") / 5.75, 0.3),
                            ),
                        ],
                        width=700,
                        height=50,
                    ),
                ],
                alignment=alignment.center
            ),
        ],
        alignment=alignment.center,
        spacing=5
    )

    # Диаграмма оси Z
    z_axis = Column(
        controls=[
            Row(
                controls=[
                    Text(
                        value="Z",
                        size=24,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Stack(
                        controls=[
                            Slider(
                                value=dimensions[2],
                                min=0,
                                max=20,
                                width=700,
                                disabled=True,
                                tooltip="По оси Z осуществляется приближение"
                                        "/удаление камеры от палеты"
                            ),
                            Container(
                                content=Column(
                                    controls=[
                                        Container(
                                            width=20,
                                            height=20,
                                            bgcolor=application_colors["text"],
                                            border_radius=border_radius.all(15),
                                        ),
                                        Text(
                                            value=str(read_from_json(
                                                "project/configuration/coordinates.json",
                                                "z_coordinate_of_the_first_cell")),
                                            color=application_colors["text"],
                                            size=16,
                                        )
                                    ],
                                    alignment=alignment.center,
                                    spacing=5
                                ),
                                offset=(read_from_json(
                                    "project/configuration/coordinates.json",
                                    "z_coordinate_of_the_first_cell") / 0.63, 0.3),
                            ),
                        ],
                        width=700,
                        height=50,
                    ),
                ],
                alignment=alignment.center
            ),
        ],
        alignment=alignment.center,
        spacing=5
    )

    # Кнопки управления режимом работы
    lower_buttons = Row(
        controls=[
            ElevatedButton(
                text="Изменить координаты",
                width=288,
                height=48,
                style=default_active_button_style,
                on_click=change_coordinates
            ),
            ElevatedButton(
                text="Сохранить координаты",
                width=288,
                height=48,
                style=default_inactive_button_style,
                on_click=save_coordinates,
                disabled=True,
            ),
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=10
    )

    right_side = Column(
        controls=[
            Text(
                "Пульт управления станцией",
                size=18,
                weight=FontWeight.BOLD,
                color=application_colors["text"]),
            Container(height=16),
            button_grid,
            Container(height=16),
            step_block,
            Container(height=16),
            x_axis,
            Container(height=16),
            y_axis,
            Container(height=16),
            z_axis,
            Container(height=16),
            lower_buttons
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    calibration_tab = Tab(
        text="Калибровка первой ячейки",
        content=Container(
            content=Column(
                controls=[
                    Row(
                        controls=[
                            Container(expand=True),
                            left_side,
                            Container(expand=True),
                            right_side,
                            Container(expand=True),
                        ],
                        alignment=MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=CrossAxisAlignment.CENTER,
                    ),
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            ),
            padding=20,
            bgcolor=application_colors["background"],
        ),
    )

    return calibration_tab
