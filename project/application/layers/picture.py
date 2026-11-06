import base64
import math
from flet import *
import cv2

from project.application.addition.colors import color_mode
from project.application.addition.load_gif_path import get_path
from project.application.addition.error_message import show_error
from project.configuration.worker import write_to_json, read_from_json
from project.station.camera.frame_settings import apply_settings_to_frame

# Глобальный флаг, отражающий, подключена ли камера к контейнеру во вкладке
BUTTON_CLICKED = 0


def create_picture_layer():
    """
    Создаёт вкладку калибровки камеры.
    Возвращает вкладку калибровки камеры - flet.Tab.
    """
    # Названия слайдеров (настроек)
    slider_titles = ["Контур, %", "Яркость, %", "Контрастность, %",
                     "Насыщенность, %", "Зернистость, %"]
    filter_titles = ["Красный фильтр, %", "Зелёный фильтр, %", "Синий фильтр, %"]
    keys_list = ["contour", "brightness", "contrast", "saturation",
                 "grain_level", "red_filter", "green_filter", "blue_filter"]

    # Текущая цветовая гамма приложения
    application_colors = color_mode()

    # Списки слайдеров и полей для синхронизации по данным
    sliders = []
    text_fields = []

    def update_slider_from_text_field(e):
        """
        Обработчик изменения значения текстового поля, синхронизирует с ним соответствующий слайдер.
        Параметры:
            событие изменения значения текстового поля e.
        """
        try:
            index = text_fields.index(e.control)
            value = float(e.control.value)

            if 0 <= value <= 100:
                sliders[index].value = value
                sliders[index].update()
                write_to_json(
                    "project/configuration/picture.json",
                    [keys_list[index]],
                    round(value))

                r = round(
                    read_from_json(
                        "project/configuration/picture.json",
                        "red_filter") * 2.55)
                g = round(
                    read_from_json(
                        "project/configuration/picture.json",
                        "green_filter") * 2.55)
                b = round(
                    read_from_json(
                        "project/configuration/picture.json",
                        "blue_filter") * 2.55)
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                color_field.value = hex_color.upper()
                color_field.update()

        except ValueError:
            pass

    def update_text_field_from_slider(e):
        """
        Обработчик изменения значения слайдера, синхронизирует с ним соответствующее текстовое поле.
        Параметры:
            событие изменения значения слайдера e.
        """
        index = sliders.index(e.control)
        text_fields[index].value = str(int(e.control.value))
        text_fields[index].update()
        write_to_json(
            "project/configuration/picture.json",
            keys_list[index],
            round(e.control.value))

        r = round(
            read_from_json(
                "project/configuration/picture.json",
                "red_filter") * 2.55)
        g = round(
            read_from_json(
                "project/configuration/picture.json",
                "green_filter") * 2.55)
        b = round(
            read_from_json(
                "project/configuration/picture.json",
                "blue_filter") * 2.55)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        color_field.value = hex_color.upper()
        color_field.update()

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
                # Захват изображения с камеры, его конвертация в Base64 и трансляция в окно
                ret, frame = cap.read()
                frame = apply_settings_to_frame(frame)
                _, buffer = cv2.imencode('.jpg', frame)
                img_base64 = base64.b64encode(buffer.tobytes()).decode('utf-8')
                if BUTTON_CLICKED == 1:
                    camera_container.content.src_base64 = img_base64
                    camera_container.update()
                else:
                    cap.release()
                    break

        except Exception:
            show_error(
                "Ошибка подключения!",
                "Ошибка OpenCV: камера не обнаружена, перезапустите программу",
                _e.page)

    def on_click_camera_disconnect(_e):
        """
        Функция-обработчик нажатия на кнопку "Отключить камеру".
        :param _e: Событие нажатия на кнопку
        :return: None
        """
        global BUTTON_CLICKED

        BUTTON_CLICKED = 0
        camera_container.content.src_base64 = ""
        camera_container.update()

    # Левый подмакет, содержит слайдеры настроек изображения
    left_column = Column(
        controls=[
            *[
                Column(
                    controls=[
                        Row(
                            controls=[
                                Container(
                                    content=Text(
                                        f"{slider_titles[i]}",
                                        font_family="Trebuchet MS",
                                        width=200,
                                        height=32,
                                        size=18,
                                        color=application_colors["text"]
                                    ),
                                    padding=Padding(24, 9, 0, 5),
                                ),
                                TextField(
                                    width=100,
                                    height=32,
                                    value=str(int(
                                            read_from_json(
                                                "project/configuration/picture.json",
                                                keys_list[i]))),
                                    text_align=TextAlign.RIGHT,
                                    content_padding=Padding(0, 0, 12, 0),
                                    color=application_colors["text"],
                                    bgcolor=application_colors["inactive"],
                                    border_color=application_colors["inactive"],
                                    focused_border_color=application_colors["text"],
                                    on_change=update_slider_from_text_field
                                ),
                            ],
                            alignment=MainAxisAlignment.SPACE_BETWEEN,
                            width=460,
                        ),
                        Slider(
                            width=480,
                            min=0,
                            max=100,
                            value=round(
                                read_from_json(
                                    "project/configuration/picture.json",
                                    keys_list[i])),
                            active_color=application_colors["text"],
                            inactive_color=application_colors["inactive"],
                            on_change=update_text_field_from_slider
                        ),
                    ],
                    spacing=0,
                    width=480,
                )
                for i in range(5)
            ],
        ],
        spacing=24,
        scroll=ScrollMode.AUTO,
    )

    # Добавление полей для ввода и слайдеров в списки синхронизации
    for i in range(5):
        text_fields.append(left_column.controls[i].controls[0].controls[1])
        sliders.append(left_column.controls[i].controls[1])

    camera_container = Container(
        content=Image(src=get_path(), fit=ImageFit.FILL, width=688, height=688),
        width=688,
        height=688,
        bgcolor=application_colors["background"],
        border_radius=12,
        alignment=alignment.center,
    )

    # Центральный подмакет, содержит надпись и контейнер для видеопотока
    center_column = Column(
        controls=[
            # Контейнер с текстом (чтобы текст был выровнен правильно)
            Container(
                content=Text(
                    "Изображение с камеры",
                    size=18,
                    text_align=TextAlign.CENTER,
                    weight=FontWeight.BOLD,
                    color=application_colors["text"],
                ),
                alignment=alignment.center,
                width=688,
            ),
            camera_container,
            Row(
                spacing=10,
                controls=[
                    Container(width=40),
                    ElevatedButton(
                        text="Подключить камеру",
                        width=288,
                        height=48,
                        style=ButtonStyle(
                            shape=RoundedRectangleBorder(radius=16),
                            bgcolor=application_colors["inactive"],
                            color=application_colors["text"],
                            overlay_color=application_colors["hover"],
                            animation_duration=300,
                            text_style=TextStyle(size=18, weight=FontWeight.BOLD),
                        ),
                        on_click=on_click_camera_connect
                    ),
                    ElevatedButton(
                        text="Отключить камеру",
                        width=288,
                        height=48,
                        style=ButtonStyle(
                            shape=RoundedRectangleBorder(radius=16),
                            bgcolor=application_colors["inactive"],
                            color=application_colors["text"],
                            overlay_color=application_colors["hover"],
                            animation_duration=300,
                            text_style=TextStyle(size=18, weight=FontWeight.BOLD),
                        ),
                        on_click=on_click_camera_disconnect
                    ),
                    Container(width=40)
                ],
                alignment=MainAxisAlignment.CENTER
            )
        ],
        spacing=16,
        alignment=MainAxisAlignment.CENTER
    )

    def hsl_to_rgb(h, s, l):
        """
        Функция преобразования HSL-значения цвета (удобнее кодировать на круге) в RGB-цвет
        :param h: Тон (угол на кругу)
        :param s: Насыщенность (всегда 0.5)
        :param l: Светлота (всегда 1)
        :return: str rgb_color
        """
        def hue_to_rgb(p, q, t):
            """
            Функция преобразования HSL-численного значения тона (H) в RGB-значение
            :param p: Параметр цветности, зависимый от q
            :param q: Параметр цветности, зависимый от l, s
            :param t: Значение цвета, зависит от р

            :return: float r or float g or float b
            """
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6

            return p

        # Преобразует координаты на кругу в RGB-цвет покомпонентно,
        # потом преобразует в строку, учитывая коэффициент коррекции 255
        if s == 0:
            r = g = b = l
        else:
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1 / 3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1 / 3)

        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    # Инициализация компонентов цветового круга
    sectors = []
    size = 250
    center = size / 2
    radius = size / 2
    for angle in range(0, 360):
        color = hsl_to_rgb(angle / 360, 1.0, 0.5)
        sectors.append(
            Container(
                width=radius,
                height=1,
                left=center,
                top=center,
                rotate=transform.Rotate(math.radians(angle), alignment=alignment.center_left),
                bgcolor=color,
            )
        )

    # Инициализация "курсора"
    cursor_size = radius // 10
    cursor = Container(
        width=cursor_size,
        height=cursor_size,
        border_radius=cursor_size,
        bgcolor=application_colors["background"],
        left=center - cursor_size / 2,
        top=center - cursor_size / 2,
        animate_position=100
    )

    def on_pan_update(e: DragUpdateEvent):
        """
        Функция-обработчик движения курсора по цветовому кругу,
        определяющая его координаты и обновляющая значение текущего
        выбранного цвета, используя hsl_to_rgb-преобразование.

        :param e: Событие перемещения курсора
        :return: None
        """
        # Вычисляем расстояние от центра
        dx = e.local_x - center
        dy = e.local_y - center
        distance = math.sqrt(dx * dx + dy * dy)

        # Ограничение курсора радиусом круга
        if distance > radius - cursor_size / 2:
            current_angle = math.atan2(dy, dx)
            dx = (radius - cursor_size / 2) * math.cos(current_angle)
            dy = (radius - cursor_size / 2) * math.sin(current_angle)

        # Обновление позиции курсора
        cursor.left = center + dx - cursor_size / 2
        cursor.top = center +  dy - cursor_size / 2

        # Вычисление текущего цвета под курсором
        current_angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        current_color = hsl_to_rgb(current_angle / 360, 1.0, 0.5)

        # Обновление информации о цвете
        if color_field.value.lower() != current_color.lower():
            color_field.value = current_color.capitalize()

        e.page.update()

    def update_cursor_from_color(e):
        """
        Функция, обновляющая положение курсора на цветовом кругу
        в зависимости от значения цвета в текстовом поле.
        :param e: Событие подтверждения значения в текстовом поле (нажатие ENTER)
        :return: None
        """
        color_str = e.control.value

        # Проверяем формат цвета (#RRGGBB)
        if not (color_str.startswith('#') and len(color_str) == 7):
            return

        try:
            # Преобразуем hex в RGB
            hex_color = color_str.lstrip('#')
            r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))

            write_to_json(
                "project/configuration/picture.json",
                "red_filter",
                round(r * 100))
            write_to_json(
                "project/configuration/picture.json",
                "green_filter",
                round(g * 100))
            write_to_json(
                "project/configuration/picture.json",
                "blue_filter",
                round(b * 100))

            text_fields[5].value = str(int(read_from_json(
                "project/configuration/picture.json",
                "red_filter")))
            text_fields[6].value = str(int(read_from_json(
                "project/configuration/picture.json",
                "green_filter")))
            text_fields[7].value = str(int(read_from_json(
                "project/configuration/picture.json",
                "blue_filter")))

            sliders[5].value = read_from_json(
                "project/configuration/picture.json",
                "red_filter")
            sliders[6].value = read_from_json(
                "project/configuration/picture.json",
                "green_filter")
            sliders[7].value = read_from_json(
                "project/configuration/picture.json",
                "blue_filter")

            # Поиск ближайшего HSL-эквивалента (обратное преобразование)
            # Поиск максимального и минимального значений
            cmax = max(r, g, b)
            cmin = min(r, g, b)
            delta = cmax - cmin

            # Вычисление светлоты
            l = (cmax + cmin) / 2

            # Вычисление насыщенности
            if delta == 0:
                h = s = 0
            else:
                s = delta / (1 - abs(2 * l - 1)) if l != 0.5 else 1

                # Вычисление значения тона
                if cmax == r:
                    h = ((g - b) / delta) % 6
                elif cmax == g:
                    h = (b - r) / delta + 2
                else:
                    h = (r - g) / delta + 4
                h *= 60

            # Корректировка угла для отображения (цветовой круг начинается с красного в 0°)
            angle = h % 360

            # Вычисление новых координат курсора
            distance = radius - cursor_size / 2
            rad = math.radians(angle)
            dx = distance * math.cos(rad)
            dy = distance * math.sin(rad)

            # Обновление позиции курсора
            cursor.left = center + dx - cursor_size / 2
            cursor.top = center + dy - cursor_size / 2

            # Обновление цвета текстового поля
            corrected_color = hsl_to_rgb(angle / 360, s, l)
            if color_field.value.lower() != corrected_color.lower():
                color_field.value = corrected_color.upper()

            e.page.update()

        except (ValueError, IndexError):
            # Некорректный формат цвета
            pass

    color_field = TextField(
        width=100,
        height=32,
        value="#343e43",
        text_align=TextAlign.CENTER,              # Выравнивание по центру
        content_padding=padding.only(top=8),      # Подгонка вертикального выравнивания
        border_color=application_colors["text"],  # Цвет контура
        bgcolor=application_colors["inactive"],   # Цвет фона
        color=application_colors["text"],         # Цвет текста
        border_width=1,                           # Толщина контура
        border_radius=4,                          # Скругление углов
        on_submit=update_cursor_from_color
    )

    gesture_detector = GestureDetector(
        content=Container(
            width=size,
            height=size,
            border_radius=radius,
            clip_behavior=ClipBehavior.HARD_EDGE,
            content=Stack(controls=sectors + [cursor])
        ),
        on_pan_update=on_pan_update,
        on_pan_start=on_pan_update
    )

    # Правый подмакет
    right_column = Column(
        controls=[
            *[
                Column(
                    controls=[
                        Row(
                            controls=[
                                Container(
                                    content=Text(
                                        f"{filter_titles[i]}",
                                        font_family="Trebuchet MS",
                                        width=200,
                                        height=32,
                                        size=18,
                                        color=(
                                            application_colors["red"] if i == 0 else
                                            application_colors["green"] if i == 1 else
                                            application_colors["active"]
                                        ),
                                    ),
                                    padding=Padding(24, 9, 0, 5),
                                ),
                                TextField(
                                    width=100,
                                    height=32,
                                    value=str(read_from_json(
                                        "project/configuration/picture.json",
                                        keys_list[i + 5])),
                                    text_align=TextAlign.RIGHT,
                                    content_padding=Padding(0, 0, 12, 0),
                                    color=application_colors["text"],
                                    bgcolor=application_colors["inactive"],
                                    border_color=application_colors["inactive"],
                                    focused_border_color=application_colors["text"],
                                    on_change=update_slider_from_text_field
                                ),
                            ],
                            alignment=MainAxisAlignment.SPACE_BETWEEN,
                            width=460,
                        ),
                        Slider(
                            width=480,
                            min=0,
                            max=100,
                            value=round(read_from_json(
                                        "project/configuration/picture.json",
                                        keys_list[i + 5])),
                            active_color=(
                                application_colors["red"] if i == 0 else
                                application_colors["green"] if i == 1 else
                                application_colors["active"]
                            ),
                            inactive_color=application_colors["inactive"],
                            on_change=update_text_field_from_slider
                        ),
                    ],
                    spacing=0,
                    width=480,
                )
                for i in range(3)
            ],
            Container(height=12),
            Row(controls=[Container(width=8),
                          Container(height=1, width=448, bgcolor=application_colors["text"]),]),
            Container(height=12),
            Row(
                controls=[
                    Container(width=1),
                    Column(
                        controls=[
                            Text("Выберите цвет при \nпомощи курсора:",
                                 size=18, color=application_colors["text"]),
                            Container(height=8),
                            color_field
                        ],
                    ),
                    Container(width=1),
                    gesture_detector
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
                width=480,
            ),
        ],
        spacing=8,
        scroll=ScrollMode.AUTO,
    )

    # Добавление слайдеров и текстовых полей в списки синхронизации
    for i in range(3):
        text_fields.append(right_column.controls[i].controls[0].controls[1])
        sliders.append(right_column.controls[i].controls[1])

    main_row = Container(
        content=Row(
            controls=[
                left_column,
                center_column,
                right_column,
            ],
            spacing=48,
            alignment=MainAxisAlignment.CENTER,
            vertical_alignment=CrossAxisAlignment.CENTER,
            expand=True,
        ),
        alignment=alignment.center,
        expand=True,
    )

    camera_tab = Tab(
        text="Настройки камеры",
        content=Container(
            content=main_row,
            bgcolor=application_colors["background"],
            padding=20,
            expand=True,
        )
    )

    return camera_tab
