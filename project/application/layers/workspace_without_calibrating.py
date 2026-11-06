import threading
from flet import *
import time

from project.alghorithms.core import main_algorithm
from project.alghorithms.idling import movement_processing
from project.application.addition.password_message import show_password_message
from project.application.addition.theme_restart_message import show_restart_message
from project.station.camera.feed import update_camera_feed
from project.application.addition.colors import color_mode
from project.application.addition.load_gif_path import get_path
from project.application.addition.object import set_object_state
from project.configuration.worker import write_to_json, read_from_json
import project.application.addition.info_page as infp
from project.station.connection import establish_connection, close_connection
from project.station.requests import move_to_home
from project.application.addition.snake_buttons import change_snake_button_color, change_button_border

def create_workspace_layer():
    """
    Функция, создающая вкладку проверки годности корпусов
    и подключающая все контролы, содержащиеся в ней,
    к обработчикам и событиям.

    :return: flet.Tab вкладка "Проверка годности корпусов"
    """
    application_colors = color_mode()
    settings_file = "project/configuration/launch.json"
    snake_buttons = []

    write_to_json(
        "project/station/statuses.json",
        "change_capture",
             -1)
    write_to_json(
        "project/station/statuses.json",
        "moved_to_cell",
        0)
    write_to_json(
        "project/station/statuses.json",
        "moved_to_home",
        0)
    write_to_json(
        "project/station/statuses.json",
        "right_view_waiting",
        0)
    write_to_json(
        "project/station/statuses.json",
        "skip_cell",
        0)
    write_to_json(
        "project/station/statuses.json",
        'start_showing',0)

    # Получаем значение установки key из JSON
    def read_setting(key, default=None):
        return read_from_json(settings_file, key) or default

    # Записываем полученное через контролы значение value установки key в JSON
    def write_setting(key, value):
        write_to_json(settings_file, key, value)

    # Поле для ввода ширины контейнера для видео с камеры
    width_input = TextField(
        label="Ширина",
        value=str(read_setting("width_image_container", 400)),
        width=120,
        height=48,
        disabled=True,
        color=application_colors["unclickable"],
        bgcolor=application_colors["top_bar"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["unclickable"]),
        tooltip="Ширина контейнера для видео с камеры в пикселях",
    )

    # Поле для ввода длины контейнера для видео с камеры
    height_input = TextField(
        label="Длина",
        value=str(read_setting("height_image_container", 400)),
        width=120,
        height=48,
        disabled=True,
        color=application_colors["unclickable"],
        bgcolor=application_colors["top_bar"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["unclickable"]),
        tooltip="Высота контейнера для видео с камеры в пикселях",
    )

    # Левый контейнер для изображений с камеры
    left_image_container = Container(
        content=Stack(
            controls=[
                Image(
                    # GIF-изображение для экрана загрузки выбирается в зависимости от цветовой темы
                    src=get_path(),
                    fit=ImageFit.FILL,
                    width=int(float(width_input.value)),
                    height=int(float(height_input.value)),
                )
            ]
        ),
        width=int(float(width_input.value)),
        height=int(float(height_input.value)),
        bgcolor=application_colors["background"],
        border_radius=10,
        alignment=alignment.center,
    )

    # Правый контейнер для изображений с камеры
    right_image_container = Container(
        content=Stack(
            controls=[
                Image(
                    # GIF-изображение экрана загрузки выбирается в зависимости от цветовой темы
                    src=get_path(),
                    fit=ImageFit.FILL,
                    width=int(float(width_input.value)),
                    height=int(float(height_input.value)),
                )
            ]
        ),
        width=int(float(width_input.value)),
        height=int(float(height_input.value)),
        bgcolor=application_colors["background"],
        border_radius=10,
        alignment=alignment.center,
    )

    # Подключение потока камеры к контейнерам
    update_camera_feed(
        left_image_container.content.controls[0],
        right_image_container.content.controls[0], snake_buttons)

    def update_image_size(_e):
        """
        Обновляет размеры контейнера с изображениями по нажатию
        кнопки "Сохранить", делает поля для ввода неактивными.

        :param _e: Событие нажатия на кнопку
        :return: None
        """
        try:
            new_width = max(200, min(700, int(float(width_input.value))))
            new_height = max(200, min(700, int(float(height_input.value))))

            for container in [left_image_container, right_image_container]:
                container.width = new_width
                container.height = new_height
                container.content.controls[0].width = new_width
                container.content.controls[0].height = new_height
                container.update()

            width_input.value, height_input.value = str(new_width), str(new_height)
            width_input.update()
            height_input.update()

            write_setting("width_image_container", new_width)
            write_setting("height_image_container", new_height)

            resize_button.bgcolor = application_colors["inactive"]
            resize_button.color = application_colors["text"]
            save_resize_button.bgcolor = application_colors["top_bar"]
            save_resize_button.color = application_colors["unclickable"]
            height_input.label_style = TextStyle(color=application_colors["unclickable"])
            width_input.label_style = TextStyle(color=application_colors["unclickable"])

            # При False кнопка кликабельна, при True - неактивна
            set_object_state(resize_button, False)
            set_object_state(width_input, True)
            set_object_state(height_input, True)
            set_object_state(save_resize_button, True)

        except ValueError:
            print("Ошибка: Введите корректные числовые значения!")

    async def resize_button_click(_e):
        """
        Активирует поля для ввода размеров контейнера для изображений по нажатию кнопки "Изменить".

        :param _e: событие нажатия на кнопку
        :return: None
        """
        pword_ok = await show_password_message(_e)

        if pword_ok:
            resize_button.bgcolor = application_colors["top_bar"]
            resize_button.color = application_colors["unclickable"]
            save_resize_button.bgcolor = application_colors["inactive"]
            save_resize_button.color = application_colors["text"]
            height_input.label_style = TextStyle(color=application_colors["text"])
            width_input.label_style = TextStyle(color=application_colors["text"])

            set_object_state(resize_button, True)
            set_object_state(width_input, False)
            set_object_state(height_input, False)
            set_object_state(save_resize_button, False)

        await _e.page.update_async()

    # Кнопка активации полей для ввода размера контейнеров для изображений.
    resize_button = ElevatedButton(
        text="Изменить",
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        on_click=resize_button_click
    )
    def change_capture_condition(num):
        if num == 1:
            write_to_json('project/station/statuses.json',"change_capture", 1)
        if num == 2:
            write_to_json('project/station/statuses.json', "change_capture", 2)
    # Кнопки для переключения камер
    cam_next = ElevatedButton(
        width = 220,
        text = '→',
        height = 80,
        on_click= lambda e: change_capture_condition(2),
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD, color=colors.BLACK),
            animation_duration=300,
        ),
        disabled=False
    )
    cam_previous = ElevatedButton(
        width= 220,
        text='←',
        height=80,
        on_click= lambda e: change_capture_condition(1),
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        disabled=False
    )
    # Кнопка сохранения введённого размера изображений.
    save_resize_button = ElevatedButton(
        text="Сохранить",
        on_click=update_image_size,
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=colors.BLACK,
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        disabled=False
    )

    #Контейнер, содержащий контролы, управляющие размером изображений, для левого блока(теперь переключение).
    controls_container = Row(
        controls=[
            cam_previous,
            cam_next,
            # resize_button,
            # width_input,
            # height_input,
            # save_resize_button
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=20,
    )

    # Левый контейнер
    left_side = Column(
        controls=[
            Text(
                "Изображение с камеры",
                size=18,
                weight=FontWeight.BOLD,
                color=application_colors["text"]),
            Container(height=16),
            left_image_container,
            Container(height=8),
            controls_container,
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    def button_click(_e):
        """
        Обрабатывает событие нажатия на одну из кнопок, обозначающих элементы палеты.
        Допускает, чтобы только одна кнопка была "активной",
        все остальные циклично делаются неактивными за счёт
        итерации по snake_buttons.

        :param _e: событие нажатия
        :return: None
        """
        nonlocal snake_buttons
        if read_from_json(
                "project/station/statuses.json",
                "moving_to_certain") == 0:
            for button in snake_buttons:
                button.style = ButtonStyle(
                    shape=RoundedRectangleBorder(radius=8),
                    bgcolor=application_colors["inactive"],
                    color=application_colors["text"],
                    text_style=TextStyle(
                        font_family="Montserrat",
                        weight=FontWeight.W_500),
                    side=BorderSide(
                        width=5,
                        color=application_colors["inactive"]
                    )
                )

            snake_buttons[int(_e.control.text) - 1].style = ButtonStyle(
                shape=RoundedRectangleBorder(radius=8),
                bgcolor=application_colors["inactive"],
                color=application_colors["text"],
                text_style=TextStyle(font_family="Montserrat", weight=FontWeight.W_500),
                side=BorderSide(
                    width=5,
                    color=application_colors["active"]
                )
            )

            if algorithm_state == "stopped":
                while read_from_json("project/station/statuses.json", 'start_showing') == 1:
                    time.sleep(0.2)
                movement_processing(int(_e.control.text) - 1, _e.page, snake_buttons)

            _e.page.update()

    def generate_snake_buttons(rows, cols):
        """
        Генерирует матрицу кнопок, визуализирующих элементы палеты, и объединяет их в ряды.
        Для синхронизации также добавляет сами кнопки в список snake_buttons.

        :param rows: количество кнопок по вертикали
        :param cols: количество кнопок по горизонтали
        :return: List[Row[ElevatedButton, ...], ...]
        """
        nonlocal snake_buttons
        snake_buttons.clear()

        buttons = []
        for i in range(rows):
            row = [
                ElevatedButton(
                    text=str(i * cols + j + 1),
                    on_click=button_click,
                    width=50,
                    height=50,
                    style=ButtonStyle(
                        shape=RoundedRectangleBorder(radius=8),
                        bgcolor=application_colors["inactive"],
                        color=application_colors["text"],
                        text_style=TextStyle(font_family="Montserrat", weight=FontWeight.W_500),
                        side=BorderSide(
                            width=2,
                            color=application_colors["inactive"]
                        )
                    )
                ) for j in range(cols)
            ]
            for button in row:
                snake_buttons.append(button)
            if i % 2 == 1:
                row.reverse()
            buttons.append(Row(controls=row, spacing=5))

        # return buttons[::-1]
        return buttons

    # Поле для ввода количества "строк" на палете
    rows_input = TextField(
        label="Строки",
        value=str(read_setting("number_of_rows", 5)),
        width=100,
        disabled=True,
        color=application_colors["unclickable"],
        bgcolor=application_colors["top_bar"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["unclickable"]),
        tooltip="Соответствует количеству схем на палете по горизонтали"
    )

    # Поле для ввода количества "столбцов" на палете
    cols_input = TextField(
        label="Столбцы",
        value=str(read_setting("number_of_columns", 5)),
        width=100,
        disabled=True,
        color=application_colors["unclickable"],
        bgcolor=application_colors["top_bar"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["unclickable"]),
        tooltip="Соответствует количеству схем на палете по вертикали"
    )

    # Поле для ввода истинного расстояния между центрами ячеек по горизонтали
    grid_width_input = TextField(
        label="Горизонталь",
        value=str(read_setting("distance_between_horizontal_centers", 50.0)),
        width=100,
        disabled=True,
        color=application_colors["unclickable"],
        bgcolor=application_colors["top_bar"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["unclickable"]),
        tooltip="Расстояние между центрами ячеек палеты по горизонтали, мм"
    )

    # Поле для ввода истинного расстояния между центрами ячеек по вертикали
    grid_height_input = TextField(
        label="Вертикаль",
        value=str(read_setting("distance_between_vertical_centers", 50.0)),
        width=100,
        disabled=True,
        color=application_colors["unclickable"],
        bgcolor=application_colors["top_bar"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["unclickable"]),
        tooltip="Расстояние между центрами ячеек палеты по вертикали, мм"
    )





    # Визуализация палеты
    button_grid = Column(
        controls=generate_snake_buttons(int(rows_input.value), int(cols_input.value)),
        spacing=5,
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )



    def update_button_grid(_e):
        """
        Повторно формирует визуализацию палеты на основе результата
        generate_snake_buttons и данных, введённых в соответствующие поля.
        Поля после получения из них данных становятся неактивными.

        :param _e: событие нажатия на кнопку "Сохранить"
        :return: None
        """
        try:
            rows, cols = int(rows_input.value), int(cols_input.value)
            grid_width = round(float(grid_width_input.value), 2)
            grid_height = round(float(grid_height_input.value), 2)

            if not (1 <= rows <= 10 and 1 <= cols <= 10):
                print("Ошибка: количество строк и столбцов должно быть от 1 до 10!")
                return

            if not (1.0 <= grid_width <= 200.0 and 1.0 <= grid_height <= 200.0):
                print("Ошибка: расстояние должно быть от 1.0 до 200.0!")
                return

            button_grid.controls = generate_snake_buttons(rows, cols)
            button_grid.update()

            write_setting("number_of_rows", rows)
            write_setting("number_of_columns", cols)
            write_setting("distance_between_horizontal_centers", grid_width)
            write_setting("distance_between_vertical_centers", grid_height)

            grid_resize_button.bgcolor = application_colors["inactive"]
            grid_resize_button.color = application_colors["text"]
            grid_save_button.bgcolor = application_colors["top_bar"]
            grid_save_button.color = application_colors["unclickable"]
            grid_height_input.label_style = TextStyle(color=application_colors["unclickable"])
            grid_width_input.label_style = TextStyle(color=application_colors["unclickable"])

            set_object_state(grid_resize_button, False)
            set_object_state(grid_width_input, True)
            set_object_state(grid_height_input, True)
            set_object_state(grid_save_button, True)

            matrix_resize_button.bgcolor = application_colors["inactive"]
            matrix_resize_button.color = application_colors["text"]
            matrix_save_button.bgcolor = application_colors["top_bar"]
            matrix_save_button.color = application_colors["unclickable"]
            rows_input.label_style = TextStyle(color=application_colors["unclickable"])
            cols_input.label_style = TextStyle(color=application_colors["unclickable"])

            set_object_state(matrix_resize_button, False)
            set_object_state(rows_input, True)
            set_object_state(cols_input, True)
            set_object_state(matrix_save_button, True)

        except ValueError:
            print("Ошибка: Введите корректные числовые значения!")

    async def grid_resize_button_click(_e):
        """
        Делает активными поля для ввода параметров визуализации палеты по нажатию кнопки "Изменить".

        :param _e: событие нажатия на кнопку
        :return: None
        """
        pword_ok = await show_password_message(_e)

        if pword_ok:
            grid_resize_button.bgcolor = application_colors["top_bar"]
            grid_resize_button.color = application_colors["unclickable"]
            grid_save_button.bgcolor = application_colors["inactive"]
            grid_save_button.color = application_colors["text"]
            grid_height_input.label_style = TextStyle(color=application_colors["text"])
            grid_width_input.label_style = TextStyle(color=application_colors["text"])

            set_object_state(grid_resize_button, True)
            set_object_state(grid_width_input, False)
            set_object_state(grid_height_input, False)
            set_object_state(grid_save_button, False)

        await _e.page.update_async()

    # Кнопка активации полей для ввода новых параметров визуализации палеты
    grid_resize_button = ElevatedButton(
        text="Изменить",
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        on_click=grid_resize_button_click
    )

    # Кнопка сохранения введённых параметров визуализации палеты
    grid_save_button = ElevatedButton(
        text="Сохранить",
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=application_colors["unclickable"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        on_click=update_button_grid,
        disabled=True
    )

    # Контейнер для кнопок управления параметрами визуализации палеты
    grid_controls_container = Row(
        controls=[
            grid_resize_button,
            grid_width_input,
            grid_height_input,
            grid_save_button,
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=20,
    )

    async def matrix_resize_button_click(_e):
        """
        Активирует поля для ввода новых характеристик палеты по нажатию кнопки "Изменить".

        :param _e: событие нажатия на кнопку
        :return: None
        """
        pword_ok = await show_password_message(_e)

        if pword_ok:
            matrix_resize_button.bgcolor = application_colors["top_bar"]
            matrix_resize_button.color = application_colors["unclickable"]
            matrix_save_button.bgcolor = application_colors["inactive"]
            matrix_save_button.color = application_colors["text"]
            cols_input.label_style = TextStyle(color=application_colors["text"])
            rows_input.label_style = TextStyle(color=application_colors["text"])

            set_object_state(matrix_resize_button, True)
            set_object_state(rows_input, False)
            set_object_state(cols_input, False)
            set_object_state(matrix_save_button, False)

        await _e.page.update_async()

    # Кнопка, активирующая поля для ввода новых характеристик палеты
    matrix_resize_button = ElevatedButton(
        text="Изменить",
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        on_click=matrix_resize_button_click
    )

    # Кнопка, сохраняющая изменения характеристик палеты
    matrix_save_button = ElevatedButton(
        text="Сохранить",
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=application_colors["unclickable"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        on_click=update_button_grid,
        disabled=True)

    # Контейнер с дополнительными кнопками управления визуализацией палеты
    additional_controls_container = Row(
        controls=[
            matrix_resize_button,
            rows_input,
            cols_input,
            matrix_save_button,
        ],
        alignment=MainAxisAlignment.CENTER,
        spacing=20,
    )

    algorithm_state = "stopped"
    algorithm_thread = None

    def run_algorithm():
        while True:
            print("Алгоритм работает")
            algorithm_last_state = main_algorithm(width_input.page, snake_buttons)

            if algorithm_last_state is None:
                on_stop(None)
                write_to_json("project/station/statuses.json", "stopped", 0)
                break

    def on_start(_e):
        nonlocal algorithm_state, algorithm_thread
        if algorithm_state == "stopped":
            start_button.bgcolor = application_colors["top_bar"]
            start_button.color = application_colors["unclickable"]
            pause_button.bgcolor = application_colors["inactive"]
            pause_button.color = application_colors["text"]
            stop_button.bgcolor = application_colors["inactive"]
            stop_button.color = application_colors["text"]

            clear_snake_but_button.bgcolor = application_colors["top_bar"]
            clear_snake_but_button.color = application_colors["unclickable"]
            click_home_button.bgcolor = application_colors["top_bar"]
            click_home_button.color = application_colors["unclickable"]

            set_object_state(start_button, True)
            set_object_state(pause_button, False)
            set_object_state(stop_button, False)
            set_object_state(clear_snake_but_button, True)
            set_object_state(click_home_button, True)

            algorithm_state = "running"
            write_to_json("project/station/statuses.json", "paused", 0)
            write_to_json("project/station/statuses.json", "stopped", 0)
            write_to_json("project/station/statuses.json", "skip_cell", 0)
            algorithm_thread = threading.Thread(target=run_algorithm, daemon=True)
            algorithm_thread.start()
            print("Алгоритм запущен")

    def on_pause(_e):
        nonlocal algorithm_state
        if algorithm_state == "running":
            pause_button.bgcolor = application_colors["top_bar"]
            pause_button.color = application_colors["unclickable"]
            continue_button.bgcolor = application_colors["inactive"]
            continue_button.color = application_colors["text"]

            stop_button.bgcolor = application_colors["top_bar"]
            stop_button.color = application_colors["unclickable"]

            set_object_state(pause_button, True)
            set_object_state(continue_button, False)
            set_object_state(stop_button, True)

            algorithm_state = "paused"
            write_to_json("project/station/statuses.json", "paused", 1)
            print("Алгоритм приостановлен")

    def on_continue(_e):
        nonlocal algorithm_state
        if algorithm_state == "paused":
            pause_button.bgcolor = application_colors["inactive"]
            pause_button.color = application_colors["text"]
            continue_button.bgcolor = application_colors["top_bar"]
            continue_button.color = application_colors["unclickable"]

            stop_button.bgcolor = application_colors["inactive"]
            stop_button.color = application_colors["text"]

            set_object_state(stop_button, False)
            set_object_state(pause_button, False)
            set_object_state(continue_button, True)

            algorithm_state = "running"
            write_to_json("project/station/statuses.json", "paused", 0)
            print("Алгоритм продолжен")

    def on_stop(_e):
        nonlocal algorithm_state
        if algorithm_state != "stopped":
            algorithm_state = "stopped"
            start_button.bgcolor = application_colors["inactive"]
            start_button.color = application_colors["text"]
            pause_button.bgcolor = application_colors["top_bar"]
            pause_button.color = application_colors["unclickable"]
            continue_button.bgcolor = application_colors["top_bar"]
            continue_button.color = application_colors["unclickable"]
            stop_button.bgcolor = application_colors["top_bar"]
            stop_button.color = application_colors["unclickable"]

            clear_snake_but_button.bgcolor = application_colors["inactive"]
            clear_snake_but_button.color = application_colors["text"]
            click_home_button.bgcolor = application_colors["inactive"]
            click_home_button.color = application_colors["text"]

            set_object_state(start_button, False)
            set_object_state(pause_button, True)
            set_object_state(continue_button, True)
            set_object_state(stop_button, True)
            set_object_state(clear_snake_but_button, False)
            set_object_state(click_home_button, False)

            write_to_json("project/station/statuses.json", "stopped", 1)
            write_to_json("project/station/statuses.json", "paused", 0)
            print("Алгоритм остановлен")

    def on_click_home(_e):
        """
        Возвращение робота на домашние координаты по всем осям.
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        nonlocal  snake_buttons, start_button, clear_snake_but_button

        connection = establish_connection(_e.page)

        click_home_button.bgcolor = application_colors["top_bar"]
        click_home_button.color = application_colors["unclickable"]
        set_object_state(click_home_button, True)

        if connection is not None:
            move_to_home(connection)
        close_connection(connection)


        click_home_button.bgcolor = application_colors["inactive"]
        click_home_button.color = application_colors["text"]
        set_object_state(click_home_button, False)



    def on_click_clear(_e):
        if  establish_connection(_e) is not None:
            for button in snake_buttons:
                change_button_border(button)
                change_snake_button_color(button, application_colors["inactive"])

    start_button = ElevatedButton(
        text="Запуск",
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        on_click=on_start,
    )

    pause_button = ElevatedButton(
        text="Пауза",
        on_click=on_pause,
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=application_colors["unclickable"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        disabled=True
    )

    continue_button = ElevatedButton(
        text="Продолжить",
        on_click=on_continue,
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=application_colors["unclickable"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        disabled=True)

    stop_button = ElevatedButton(
        text="Стоп",
        on_click=on_stop,
        width=120,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["top_bar"],
            color=application_colors["unclickable"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        disabled=True
    )

    click_home_button = ElevatedButton(
        text="Откалибровать",
        on_click=on_click_home,
        width=150,
        height=48,
        expand=True,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        disabled=False)

    clear_snake_but_button = ElevatedButton(
        text="Очистить ячейки",
        on_click=on_click_clear,
        width=180,
        height=48,
        expand=True,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=20),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=16, weight=FontWeight.BOLD),
            animation_duration=300,
        ),
        disabled=False
    )


    right_buttons = Container(
        content = Column(
            controls=[
                Row([
                    start_button,
                    pause_button,
                    continue_button,
                    stop_button,
                ]),
                Row([
                    clear_snake_but_button,
                    click_home_button
                ]),
            ],
            alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.CENTER,
            spacing=15,
            ),
            padding=padding.only(top=15)
        )


    right_side = Column(
        controls=[
            Container(height=18),
            Text(
                "Обнаружение дефектов",
                size=20,
                weight=FontWeight.BOLD,
                color=application_colors["text"]),
            Container(height=12),
            right_image_container,
            right_buttons,
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    matrix_column = Column(
        controls=[
            Text(
                "Результаты инспекции",
                size=18,
                weight=FontWeight.BOLD,
                color=application_colors["text"]),
            Container(height=16),
            button_grid,
            Container(height=35),
            infp.info_page(),
            # used_networks_list
            # grid_controls_container,
            # Container(height=10),
            # additional_controls_container,
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    def update_colors(_e):
        show_restart_message("Сменить фон приложения?",
                             "Приложение будет перезагружено. "
                             "Если перезагрузка не началась автоматически, запустите его вручную.",
                             _e.page)
        _e.page.update()

    switch_theme_button = IconButton(
                icon=icons.DARK_MODE_OUTLINED,
                icon_color=application_colors["text"],
                tooltip="Сменить фон приложения",
                on_click=update_colors,
            )

    workspace_tab = Tab(
        text="Проверка годности корпусов",
        content=Container(
            content=Column(
                controls=[
                    Row(
                        controls=[
                            Column(
                                controls=[
                                    switch_theme_button,
                                    Container(height=800)
                                ]
                            ),
                            left_side,
                            Container(expand=True),
                            matrix_column,
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

    return workspace_tab
