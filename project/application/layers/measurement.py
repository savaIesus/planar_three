from threading import Timer
import math
import base64
import time
from flet import *
from flet import canvas
import cv2

from project.application.addition.colors import color_mode
from project.application.addition.load_gif_path import get_path
from project.configuration.worker import write_to_json, read_from_json
from project.application.addition.error_message import show_error
from project.station.camera.frame_settings import apply_settings_to_frame

# Глобальный флаг, отражающий, подключена ли камера к контейнеру во вкладке
BUTTON_CLICKED = 0


def create_measurements_tab():
    """
    Функция, создающая вкладку измерения объектов на изображении.
    Возвращает:
        вкладку flet.Tab.
    """
    # Цвета приложения и названия выбираемых опций
    application_colors = color_mode()
    measurement_units = ["Миллиметры (1 мм)", "Микрометры (1 мкм)", "Пиксели (1 пкс)"]
    tool_symbols = ["↔", "○", "▢", "△"]
    tool_titles = ["Построение отрезка линии", "Построение эллипса",
                   "Построение прямоугольника", "Построение треугольника"]
    current_unit = read_from_json(
        "project/configuration/measure.json",
        "measure_units")

    paint_constant = Paint(
        stroke_width=4,
        style=PaintingStyle.STROKE,
        color=application_colors["red"])

    # Список кнопок, отвечающих за выбор инструмента измерения. Обеспечивает синхронизацию
    tool_buttons = []

    # Состояние рисования
    current_tool = None
    start_point = None
    end_point = None
    shapes = []        # Список фигур, рисование которых завершено
    temp_shape = None  # Фигура, рисование которой ещё идёт
    temp_mes_text = None
    drawing = False    # Флаг состояния рисования (рисуется ли новая фигура в данный момент)
    drawing_canvas = canvas.Canvas(width=720, height=720, shapes=shapes)
    current_coefficient = read_from_json(
        "project/configuration/measure.json",
        "translation_coefficient")

    # Переменные для оптимизации обработки мыши
    last_mouse_time = 0
    mouse_delay = 0.01  # 10 мс
    mouse_debounce_timer = None

    mes_text = Text(
        value="",
        size=14,
        color=application_colors["text"],
        weight=FontWeight.W_500,
        bgcolor=application_colors["active"],
        width=720,
        text_align=TextAlign.CENTER
    )

    def calculate_dimensions(x1, y1, x2, y2):
        """
        Вычисляет размеры измерительных фигур в зависимости от
        инструмента, коэффициента перевода и единиц измерения.

        :param x1: x-координата начальной точки
        :param y1: y-координата начальной точки
        :param x2: x-координата конечной точки
        :param y2: y-координата конечной точки
        :return: str - текст, который будет выведен рядом с фигурой
        """
        # Выбранные единицы измерения
        nonlocal current_unit, current_coefficient

        # Если инструмент измерения не определён, возвращаем координаты конечной точки
        if current_tool is None:
            return "", x2, y2

        width = abs(x2 - x1)
        height = abs(y2 - y1)
        length = math.hypot(width, height)
        coefficient = current_coefficient

        # Текст располагается по центру фигуры
        text_x = x1 + (x2 - x1) * 0.3
        text_y = (y1 + y2) / 2

        if current_tool == 1:  # Отрезок
            if current_unit == "Миллиметры (1 мм)":
                return f"Длина: {coefficient * length:.2f} мм", text_x, text_y
            elif current_unit == "Пиксели (1 пкс)":
                return f"Длина: {length:.2f} пкс", text_x, text_y
            elif current_unit == "Микрометры (1 мкм)":
                return f"Длина: {coefficient * 1000 * length:.2f} мкм", text_x, text_y

        elif current_tool == 0:  # Эллипс
            semi_major_axis = width / 2
            semi_minor_axis = height / 2
            if current_unit == "Миллиметры (1 мм)":
                return (
                    f"Полуось a: {coefficient * semi_major_axis:.2f} мм,"
                    f" \nПолуось b: {coefficient * semi_minor_axis:.2f} мм",
                    text_x, text_y
                )
            elif current_unit == "Пиксели (1 пкс)":
                return (
                    f"Полуось a: {semi_major_axis:.2f} пкс,"
                    f" \nПолуось b: {semi_minor_axis:.2f} пкс",
                    text_x, text_y
                )
            elif current_unit == "Микрометры (1 мкм)":
                return (
                    f"Полуось a: {coefficient * 1000 * semi_major_axis:.2f} мкм,"
                    f" \nПолуось b: {coefficient * 1000 * semi_minor_axis:.1f} мкм",
                    text_x, text_y
                )

        elif current_tool == 2:  # Прямоугольник
            if current_unit == "Миллиметры (1 мм)":
                return (f"Ширина: {coefficient * width:.2f} мм,"
                        f" \nВысота: {coefficient * height:.2f} мм"), text_x, text_y
            elif current_unit == "Пиксели (1 пкс)":
                return (f"Ширина: {width:.2f} пкс,"
                        f" \nВысота: {height:.2f} пкс"), text_x, text_y
            elif current_unit == "Микрометры (1 мкм)":
                return (f"Ширина: {coefficient * 1000 * width:.2f} мкм,"
                        f" \nВысота: {coefficient * 1000 * height:.2f} мкм"), text_x, text_y

        elif current_tool == 3:  # Треугольник
            base = width
            height = abs(y2 - y1)
            if current_unit == "Миллиметры (1 мм)":
                return (f"Основание: {coefficient * base:.2f} мм,"
                        f" \nВысота: {coefficient * height:.2f} мм"), text_x, text_y
            elif current_unit == "Пиксели (1 пкс)":
                return (f"Основание: {base:.2f} пкс,"
                        f" \nВысота: {height:.2f} пкс"), text_x, text_y
            elif current_unit == "Микрометры (1 мкм)":
                return (f"Основание: {coefficient * 1000 * base:.2f} мкм,"
                        f" \nВысота: {coefficient * 1000 * height:.2f} мкм"), text_x, text_y

        return "", x2, y2

    def update_size_text(x1, y1, x2, y2):
        """
        Обновляет текст, выводимый рядом с отрисовываемой фигурой,
        вычисляя его значение через calculate_dimensions.

        :param x1: x-координата начальной точки
        :param y1: y-координата начальной точки
        :param x2: x-координата конечной точки
        :param y2: y-координата конечной точки
        :return:
        """
        nonlocal temp_mes_text
        text_value, text_x, text_y = calculate_dimensions(x1, y1, x2, y2)

        # Создаем или обновляем текст на холсте canvas
        if not temp_mes_text or temp_mes_text.text != text_value:
            temp_mes_text = canvas.Text(
                x=text_x,
                y=text_y,
                text=text_value,
                style=TextStyle(
                    weight=FontWeight.BOLD,
                    size=16,
                    color=application_colors["red"],
                    bgcolor=Colors.WHITE),
                text_align=TextAlign.CENTER,
            )

    def update_canvas():
        """
        Обновляет холст canvas, на котором осуществляется рисование - добавляет туда фигуры и текст.
        """
        current_shapes = shapes.copy()
        if drawing:
            if temp_shape:
                current_shapes.append(temp_shape)
            if temp_mes_text:
                current_shapes.append(temp_mes_text)

        if drawing_canvas.shapes != current_shapes:
            drawing_canvas.shapes = current_shapes
            if drawing_canvas.page:
                drawing_canvas.page.update()

    def on_mouse_down(e):
        """
        Обработчик "зажатия" мыши. Пока кнопка мыши "зажата", рисование фигуры продолжается.
        :param e: событие "зажатия" мыши e
        """
        nonlocal start_point, drawing, temp_shape, temp_mes_text, current_coefficient
        if current_tool is None:
            return

        drawing = True
        current_coefficient = read_from_json(
        "project/configuration/measure.json",
        "translation_coefficient")
        start_point = (e.local_x, e.local_y)
        temp_mes_text = None
        update_canvas()

    def on_mouse_move(e):
        """
        Обработчик движения мыши. Если флаг рисования поднят
        (мышь "зажата"), то изменяет фигуру, которая сейчас строится.
        :param e: событие перемещения мыши e.
        """
        nonlocal last_mouse_time, mouse_debounce_timer, mouse_delay

        current_time = time.time()
        if current_time - last_mouse_time < mouse_delay:
            return

        last_mouse_time = current_time

        if mouse_debounce_timer is not None:
            mouse_debounce_timer.cancel()

        mouse_debounce_timer = Timer(mouse_delay, lambda: process_mouse_move(e))
        mouse_debounce_timer.start()

    def process_mouse_move(e):
        nonlocal temp_shape, temp_mes_text, start_point, drawing
        if not drawing or current_tool is None or start_point is None:
            return

        x1, y1 = start_point
        x2, y2 = e.local_x, e.local_y

        # Обновляем текст
        update_size_text(x1, y1, x2, y2)

        # Строим обновляемую фигуру
        if current_tool == 1:  # Отрезок
            temp_shape = canvas.Line(
                x1=x1, y1=y1, x2=x2, y2=y2,
                paint=paint_constant
            )
        elif current_tool == 0:  # Окружность
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            temp_shape = canvas.Oval(
                x=min(x1, x2), y=min(y1, y2),
                width=width, height=height,
                paint=paint_constant
            )
        elif current_tool == 2:  # Прямоугольник
            temp_shape = canvas.Rect(
                x=min(x1, x2), y=min(y1, y2),
                width=abs(x2 - x1), height=abs(y2 - y1),
                paint=paint_constant
            )
        elif current_tool == 3:  # Треугольник
            triangle = canvas.Path(
                [
                    canvas.Path.MoveTo(x1, y1),
                    canvas.Path.LineTo(x2, y2),
                    canvas.Path.LineTo(x1 - (x2 - x1), y2),
                    canvas.Path.Close(),
                    canvas.Path.MoveTo(x1, y1),
                    canvas.Path.LineTo(((x1 - (x2 - x1))+x2) / 2, y2),
                ],
                paint=paint_constant
            )
            temp_shape = triangle

        update_canvas()

    def on_mouse_up(e):
        """
        Обработчик события "отпускания" кнопки мыши. Если кнопка мыши больше не "зажата",
        опускает флаг рисования и строит завершённые, необновляемые фигуры.
        :param e: событие "отпускания" мыши e.
        """
        nonlocal start_point, shapes, temp_shape, temp_mes_text, drawing
        if current_tool is None or start_point is None:
            return

        drawing = False
        x1, y1 = start_point
        x2, y2 = e.local_x, e.local_y

        # Создаем необновляемую фигуру
        if current_tool == 1:  # Отрезок
            shapes.append(canvas.Line(
                x1=x1, y1=y1, x2=x2, y2=y2,
                paint=paint_constant
            ))
        elif current_tool == 0:  # Окружность
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            ellipse = canvas.Oval(
                x=min(x1, x2), y=min(y1, y2),
                width=width, height=height,
                paint=paint_constant
            )
            shapes.append(ellipse)
        elif current_tool == 2:  # Прямоугольник
            shapes.append(canvas.Rect(
                x=min(x1, x2), y=min(y1, y2),
                width=abs(x2 - x1), height=abs(y2 - y1),
                paint=paint_constant
            ))
        elif current_tool == 3:  # Треугольник
            triangle = canvas.Path(
                paint=paint_constant
            )
            triangle.MoveTo(x1, y1)
            triangle.LineTo(x2, y2)
            triangle.LineTo(x1 - (x2 - x1), y2)
            triangle.Close()
            triangle.MoveTo(x1, y1)
            triangle.LineTo((x1 + x2) / 2, y2)
            shapes.append(triangle)

        start_point = None
        temp_shape = None
        temp_mes_text = None
        update_canvas()

    drawing_detector = GestureDetector(
        content=drawing_canvas,
        on_tap_down=on_mouse_down,
        on_tap_up=on_mouse_up,
        on_pan_update=on_mouse_move,
        mouse_cursor=MouseCursor.BASIC
    )

    drawing_container = Container(
        content=Column(
            [drawing_detector, mes_text],
            spacing=1),
        width=720,
        height=720,
        bgcolor=colors.TRANSPARENT,
        border_radius=12,
        alignment=alignment.center
    )

    def clear_canvas(_e):
        """
        Вспомогательная функция очистки холста, на котором ведётся рисование.
        :param _e: Событие нажатия на кнопку "Очистить окно"
        :return: None
        """
        nonlocal shapes, temp_shape, temp_mes_text
        shapes.clear()
        temp_mes_text = None
        temp_shape = None
        update_canvas()

    def update_slider_from_text_field(e):
        """
        Обработчик изменения значения текстового поля, синхронизирует с ним соответствующий слайдер.
        Параметры:
            событие изменения значения текстового поля e.
        """
        nonlocal text_field
        nonlocal slider

        try:
            value = float(e.control.value)
            if 0 <= value <= 100:
                if value <= 1:
                    slider.value = value * 50
                elif value > 1:
                    slider.value = (value / 2) + 50
                slider.update()
                write_to_json(
                    "project/configuration/measure.json",
                    "translation_coefficient",
                    value)
        except ValueError:
            pass

        e.page.update()

    def update_text_field_from_slider(e):
        """
        Обработчик изменения значения слайдера, синхронизирует с ним соответствующее текстовое поле.
        Параметры:
            событие изменения значения слайдера e.
        """
        nonlocal text_field
        nonlocal slider

        coefficient = int(e.control.value)
        if coefficient == 50:
            coefficient = 1
        elif coefficient > 50:
            coefficient = 2 * (coefficient - 50)
        elif coefficient < 50:
            coefficient = (2 * coefficient) / 100
        write_to_json(
            "project/configuration/measure.json",
            "translation_coefficient",
            coefficient)
        text_field.value = str(coefficient)
        text_field.update()
        e.page.update()

    def on_option_change(e):
        """
        Вспомогательная функция-обработчик выбора другой единицы измерения в выпадающем списке.
        :param e: Событие нажатия на другую опцию в выпадающем списке
        :return: None
        """
        nonlocal current_unit
        current_unit = e.control.value
        write_to_json(
            "project/configuration/measure.json",
            "measure_unit",
            e.control.value)

    def tool_changed(_e):
        """
        Обработчик события нажатия на кнопку выбора измерительного
        инструмента. Позволяет иметь только одну активную
        (ту, которую нажали) кнопку, остальные деактивирует.
        :Параметры:
            событие нажатия на кнопку e.
        """
        nonlocal tool_buttons, current_tool

        # Деактивация всех кнопок
        for button in tool_buttons:
            button.style = ButtonStyle(
                        padding=0,
                        shape=RoundedRectangleBorder(radius=14),
                        bgcolor=application_colors["inactive"],
                        color=application_colors["text"],
                        overlay_color=application_colors["hover"],
                        animation_duration=300,
                        text_style=TextStyle(size=28, weight=FontWeight.BOLD)
                    )

        # Выборочная активация нажатой кнопки
        if _e.control.text == tool_symbols[0]:
            tool_buttons[0].style = ButtonStyle(
                padding=0,
                shape=RoundedRectangleBorder(radius=14),
                bgcolor=application_colors["active"],
                color=application_colors["text"],
                overlay_color=application_colors["hover"],
                animation_duration=300,
                text_style=TextStyle(size=28, weight=FontWeight.BOLD)
            )
            current_tool = 1
        elif _e.control.text == tool_symbols[1]:
            tool_buttons[1].style = ButtonStyle(
                padding=0,
                shape=RoundedRectangleBorder(radius=14),
                bgcolor=application_colors["active"],
                color=application_colors["text"],
                overlay_color=application_colors["hover"],
                animation_duration=300,
                text_style=TextStyle(size=28, weight=FontWeight.BOLD)
            )
            current_tool = 0
        elif _e.control.text == tool_symbols[2]:
            tool_buttons[2].style = ButtonStyle(
                padding=0,
                shape=RoundedRectangleBorder(radius=14),
                bgcolor=application_colors["active"],
                color=application_colors["text"],
                overlay_color=application_colors["hover"],
                animation_duration=300,
                text_style=TextStyle(size=28, weight=FontWeight.BOLD)
            )
            current_tool = 2
        elif _e.control.text == tool_symbols[3]:
            tool_buttons[3].style = ButtonStyle(
                padding=0,
                shape=RoundedRectangleBorder(radius=14),
                bgcolor=application_colors["active"],
                color=application_colors["text"],
                overlay_color=application_colors["hover"],
                animation_duration=300,
                text_style=TextStyle(size=28, weight=FontWeight.BOLD)
            )
            current_tool = 3

        _e.page.update()

    def on_click_camera_connect(_e):
        """
        Функция-обработчик события нажатия на кнопку "Подключить камеру".
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
            show_error("Ошибка подключения!",
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

    # Элементы левого столбца - заголовок, выпадающие списки, слайдер, кнопка очистки окна
    units_label = Text(
        "Единицы измерения", size=18, color=application_colors["text"], weight=FontWeight.BOLD
    )

    units_dropdown = Dropdown(
        width=480,
        height=48,
        options=[dropdown.Option(unit) for unit in measurement_units],
        value = read_from_json(
            "project/configuration/measure.json",
            "measure_unit"),
        on_change=on_option_change,

        text_size=14,
        text_style=TextStyle(weight=FontWeight.W_500),
        color=application_colors["text"],
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        border_radius=12,

        select_icon=Icon(
            name=icons.ARROW_DROP_DOWN_ROUNDED,
            size=48,
            color=application_colors["text"],
            offset=transform.Offset(0.25, -0.89)
        ),
        elevation=4,
    )

    tools_label = Text(
        "Инструменты измерения", size=18, color=application_colors["text"], weight=FontWeight.BOLD
    )

    tools_list = Column(
        spacing=5,
        controls=[
            Row([
                ElevatedButton(
                    text=tool_symbols[i],
                    width=64,
                    height=64,
                    style=ButtonStyle(
                        padding=0,
                        shape=RoundedRectangleBorder(radius=14),
                        bgcolor=application_colors["inactive"],
                        color=application_colors["text"],
                        overlay_color=application_colors["hover"],
                        animation_duration=300,
                        text_style=TextStyle(size=28, weight=FontWeight.BOLD)
                    ),
                    on_click=tool_changed
                ),
                Text(tool_titles[i], size=18, color=application_colors["text"])
            ])
            for i in range(4)
        ],
        alignment=MainAxisAlignment.START
    )

    # Добавление всех кнопок выбора инструментов измерения в список
    for i in range(4):
        tool_buttons.append(tools_list.controls[i].controls[0])

    scale_label = Text(
        "Преобразование пикселей в единицы измерения", size=18,
        color=application_colors["text"], weight=FontWeight.BOLD
    )

    scale_slider_value = read_from_json(
        "project/configuration/measure.json",
        "translation_coefficient")
    if scale_slider_value <= 1:
        scale_slider_value = scale_slider_value * 50
    elif scale_slider_value > 1:
        scale_slider_value = (scale_slider_value / 2) + 50

    scale_slider = Column(
        controls=[
            Row(
                controls=[
                    Container(
                        content=Text(
                            "Коэффициент (логарифмическая шкала)",
                            font_family="Trebuchet MS",
                            width=200,
                            height=32,
                            size=18,
                            color=application_colors["text"]
                        ),
                        padding=Padding(24, 9, 0, 5),
                        ),
                        TextField(
                            width=80,
                            height=32,
                            value=str(read_from_json(
                                "project/configuration/measure.json",
                                "translation_coefficient")),
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
                    value=scale_slider_value,
                    active_color=application_colors["text"],
                    inactive_color=application_colors["inactive"],
                    on_change=update_text_field_from_slider
                ),
            ],
            spacing=0,
            width=480,
        )

    # Сохранение ссылок на поле для ввода и слайдер для дальнейшей синхронизации
    text_field = scale_slider.controls[0].controls[1]
    slider = scale_slider.controls[1]

    clear_button = ElevatedButton(
        text="Очистить окно от инструментов измерения",
        width=480,
        height=48,
        style=ButtonStyle(
            shape=RoundedRectangleBorder(radius=16),
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=18, weight=FontWeight.BOLD),
            overlay_color=application_colors["hover"],
            animation_duration=300,
        ),
        on_click=clear_canvas
    )

    left_column = Column(
        spacing=15,
        controls=[
            units_label,
            Container(height=1),
            units_dropdown,
            Container(height=24),
            tools_label,
            Container(height=1),
            tools_list,
            Container(height=24),
            scale_label,
            Container(height=1),
            scale_slider,
            Container(height=16),
            clear_button
        ],
        alignment=MainAxisAlignment.CENTER
    )

    # Элементы правого столбца - заголовок, контейнер для
    # изображения, кнопки управления подключением камерой
    camera_label = Text(
        "Изображение с камеры", size=18, color=application_colors["text"], weight=FontWeight.BOLD
    )

    camera_container = Container(
        content=Image(src=get_path(), fit=ImageFit.FILL, width=720, height=720),
        width=720,
        height=720,
        bgcolor=application_colors["background"],
        border_radius=12,
        alignment=alignment.center,
    )

    camera_controls = Row(
        spacing=10,
        controls=[
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
            )
        ],
        alignment=MainAxisAlignment.CENTER
    )

    right_column = Column(
        spacing=15,
        controls=[
            camera_label,
            Container(height=1),
            Stack(controls=[camera_container, drawing_container], width=720, height=720),
            Container(height=1),
            camera_controls
        ],
        alignment=MainAxisAlignment.START,
        horizontal_alignment=CrossAxisAlignment.CENTER
    )

    measurement_tab = Tab(
        text="Измерение объектов на изображении",
        content=Container(
            content=Column(
                controls=[
                    Row(
                        controls=[
                            Container(expand=True),
                            left_column,
                            Container(expand=True),
                            right_column,
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

    return measurement_tab
