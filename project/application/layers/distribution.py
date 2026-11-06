import os
import threading
import json
import time
import serial
import flet as ft


def create_layout_control_tab():
    application_colors = {
        "red": "#ea1a1a",
        "light_red": "#f04242",
        "text": "#343e43",
        "hover": "#40a8ee",
        "green": "#2bda6a",
        "active": "#1592e6",
        "top_bar": "#e0e0e0",
        "inactive": "#cecece",
        "unclickable": "#9d9d9d",
        "active_unclickable": "#3584b9",
        "background": "#f5f5f5",
    }

    selected_protocol_path = {"path": None}
    file_protocol_field = ft.TextField(
        label="Файл-протокол",
        value="Выберите файл-протокол инспекции",
        width=420,
        border_radius=16,
        text_style=ft.TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=ft.TextStyle(color=application_colors["text"])
    )

    def file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            path = e.files[0].path
            selected_protocol_path["path"] = path
            file_protocol_field.value = os.path.basename(path)
            file_protocol_field.update()

    file_picker = ft.FilePicker(on_result=file_picked)

    select_file_button = ft.ElevatedButton(
        content=ft.Text(
            value="Выбрать файл",
            size=20,
            weight=ft.FontWeight.BOLD
        ),
        on_click=lambda e: file_picker.pick_files(
            initial_directory="project/configuration/protocols/json"),
        style=ft.ButtonStyle(
            color=application_colors["text"],
            bgcolor=application_colors["inactive"],
            padding=20
        ),
        width=420
    )

    start_layout_button = ft.ElevatedButton(
        content=ft.Text(
            value="Запустить раскладку корпусов",
            size=20,
            weight=ft.FontWeight.BOLD
        ),
        style=ft.ButtonStyle(
            color=application_colors["text"],
            bgcolor=application_colors["active"],
            padding=20
        ),
        width=420
    )

    def read_printer_response(serial_connection):
        while True:
            response = serial_connection.readline().decode(errors="ignore").strip()
            if response:
                print(f"<<< {response}")
                if "error" in response.lower():
                    print("⚠ Ошибка принтера!")
                if response.lower() == "ok":
                    break

    def send_command(serial_connection, command):
        try:
            print(f">>> {command}")
            serial_connection.write(f"{command}\r\n".encode())
            read_printer_response(serial_connection)
            return True
        except Exception as e:
            print(f"Ошибка отправки: {str(e)}")
            return False

    def run_distribution():
        try:
            protocol_path = selected_protocol_path["path"]
            if not protocol_path:
                print("Файл протокола не выбран")
                return

            serial_connection = serial.Serial(
                port="COM6",
                baudrate=115200,
                timeout=1
            )

            time.sleep(2)
            serial_connection.reset_input_buffer()
            send_command(serial_connection, "G28")

            # Точные координаты углов
            left_top_x = -90.0
            left_top_y = 87.0
            right_top_x = 80.0
            right_top_y = 82.0
            left_bottom_x = -94.0
            left_bottom_y = -82.0
            right_bottom_x = 70.0
            right_bottom_y = -92.0

            # ИНДИВИДУАЛЬНЫЕ ПОПРАВКИ ДЛЯ КОНКРЕТНЫХ ЯЧЕЕК
            # Формат: (ряд, колонка): (поправка_X, поправка_Y)
            # X левее "-", правее "+"; Y выше "-", ниже "+"
            cell_corrections = {
                (0, 0): (0.5, 0.0),
                (0, 1): (0.0, 0.0),
                (0, 2): (0.0, 0.0),
                (0, 3): (0.0, 0.0),
                (0, 4): (0.0, 0.0),
                (0, 5): (0.0, 0.0),
                (0, 6): (0.0, 0.0),
                (0, 7): (0.0, 0.0),
                (0, 8): (0.0, 0.0),
                (0, 9): (0.5, 0.5),
                # РЯД 1 (2-й ряд)
                (1, 0): (0.0, -0.3),
                (1, 1): (0.0, 0.0),
                (1, 2): (0.0, 0.0),
                (1, 3): (0.0, 0.0),
                (1, 4): (0.0, 0.0),
                (1, 5): (0.0, 0.0),
                (1, 6): (0.0, 0.0),
                (1, 7): (0.0, 0.0),
                (1, 8): (0.0, 0.0),
                (1, 9): (0.0, 0.0),
                # РЯД 2 (3-й ряд)
                (2, 0): (0.0, -0.3),
                (2, 1): (0.0, 0.0),
                (2, 2): (0.0, 0.0),
                (2, 3): (0.0, 0.0),
                (2, 4): (0.0, 0.0),
                (2, 5): (0.0, 0.0),
                (2, 6): (0.0, 0.0),
                (2, 7): (0.0, 0.0),
                (2, 8): (0.0, 0.0),
                (2, 9): (0.0, 0.3),
                # РЯД 3 (4-й ряд)
                (3, 0): (0.0, 0.0),
                (3, 1): (0.0, 0.0),
                (3, 2): (0.0, 0.0),
                (3, 3): (0.0, 0.0),
                (3, 4): (0.0, 0.0),
                (3, 5): (0.0, 0.0),
                (3, 6): (0.0, 0.0),
                (3, 7): (0.0, 0.0),
                (3, 8): (0.0, 0.0),
                (3, 9): (0.0, 0.3),
                # РЯД 4 (5-й ряд)
                (4, 0): (0.0, 0.0),
                (4, 1): (-0.3, 0.0),
                (4, 2): (0.0, 0.0),
                (4, 3): (0.0, 0.0),
                (4, 4): (0.0, 0.0),
                (4, 5): (0.0, 0.0),
                (4, 6): (0.0, 0.0),
                (4, 7): (0.0, 0.0),
                (4, 8): (0.0, 0.0),
                (4, 9): (-0.3, 0.3),
                # РЯД 5 (6-й ряд)
                (5, 0): (-0.5, 0.0),
                (5, 1): (-0.5, 0.0),
                (5, 2): (-0.3, 0.0),
                (5, 3): (-0.5, 0.0),
                (5, 4): (-0.5, 0.0),
                (5, 5): (-0.5, 0.0),
                (5, 6): (-0.5, 0.0),
                (5, 7): (-0.5, 0.0),
                (5, 8): (-0.5, 0.0),
                (5, 9): (-0.3, 0.3),
                # РЯД 6 (7-й ряд)
                (6, 0): (-0.3, 0.0),
                (6, 1): (-0.3, 0.0),
                (6, 2): (-0.5, 0.0),
                (6, 3): (-0.5, 0.0),
                (6, 4): (-0.5, 0.0),
                (6, 5): (-0.5, 0.0),
                (6, 6): (-0.5, 0.0),
                (6, 7): (-0.5, 0.0),
                (6, 8): (-0.5, 0.0),
                (6, 9): (-0.5, 0.5),
                # РЯД 7 (8-й ряд)
                (7, 0): (-0.5, 0.0),
                (7, 1): (-0.5, 0.0),
                (7, 2): (-0.3, 0.0),
                (7, 3): (-0.5, 0.0),
                (7, 4): (-0.5, 0.0),
                (7, 5): (-0.5, 0.0),
                (7, 6): (-0.5, 0.0),
                (7, 7): (-0.3, 0.3),
                (7, 8): (-0.5, 0.0),
                (7, 9): (-0.5, 0.0),
                # РЯД 8 (9-й ряд)
                (8, 0): (-0.5, 0.0),
                (8, 1): (-0.5, 0.0),
                (8, 2): (-0.5, 0.0),
                (8, 3): (-0.5, 0.0),
                (8, 4): (-0.5, 0.0),
                (8, 5): (-0.3, 0.0),
                (8, 6): (-0.5, 0.0),
                (8, 7): (-0.5, 0.0),
                (8, 8): (-0.5, 0.0),
                (8, 9): (-0.5, 0.0),
                # РЯД 9 (10-й ряд)
                (9, 0): (-0.5, 0.0),
                (9, 1): (-0.5, 0.0),
                (9, 2): (-0.3, 0.0),
                (9, 3): (-0.3, 0.0),
                (9, 4): (-0.3, 0.0),
                (9, 5): (-0.5, 0.0),
                (9, 6): (-0.5, 0.0),
                (9, 7): (-0.5, 0.0),
                (9, 8): (-0.5, -0.3),
                (9, 9): (-0.5, 0.3),
            }

            print("\nУгловые координаты:")
            print(f"[0,0]: X={left_top_x}, Y={left_top_y}")
            print(f"[0,9]: X={right_top_x}, Y={right_top_y}")
            print(f"[9,0]: X={left_bottom_x}, Y={left_bottom_y}")
            print(f"[9,9]: X={right_bottom_x}, Y={right_bottom_y}")

            start_z = 45.0
            pickup_z = 31.0
            feed_rate = 4000  # Удвоено с 2000 до 4000

            defect_x = -9.0
            defect_y_starter = 87.5
            defect_y = 139.0
            defect_z_lower = 80.0
            defect_z_upper = 105.0

            with open(protocol_path, 'r', encoding='utf-8') as file:
                protocol = json.load(file)

            defects = {}
            for defect in protocol["defects"]:
                key = (defect["vert"], defect["hor"])
                defects[key] = defect["type"]

            print("\nЗАГРУЖЕНЫ ДЕФЕКТЫ:")
            for (v, h), t in defects.items():
                print(f"  Ряд {v}, Колонка {h}: {t}")

            # Создание матрицы с учётом поправок
            positions = []
            for row in range(10):
                row_positions = []
                v = row / 9.0

                for col in range(10):
                    u = col / 9.0

                    # Базовая билинейная интерполяция
                    x_top = left_top_x * (1 - u) + right_top_x * u
                    x_bottom = left_bottom_x * (1 - u) + right_bottom_x * u
                    x = x_top * (1 - v) + x_bottom * v

                    y_top = left_top_y * (1 - u) + right_top_y * u
                    y_bottom = left_bottom_y * (1 - u) + right_bottom_y * u
                    y = y_top * (1 - v) + y_bottom * v

                    # Применение индивидуальной поправки к каждой ячейке
                    cell_key = (row, col)
                    if cell_key in cell_corrections:
                        corr_x, corr_y = cell_corrections[cell_key]
                        x += corr_x
                        y += corr_y
                        print(
                            f"  Применена поправка для [{row},{col}]: X{
                            corr_x:+.1f}, Y{corr_y:+.1f}"
                        )

                    row_positions.append((x, y))
                positions.append(row_positions)

            # Проверка проблемных рядов
            print("\nКонтрольные точки по рядам:")
            for row in [8, 9]:
                print(f"\nРяд {row}:")
                for col in [5, 6, 7, 8, 9]:
                    x, y = positions[row][col]
                    print(f"  [{row},{col}]: X={x:.2f}, Y={y:.2f}")

            defect_positions = []  # каждый элемент: (x, y, row, col, defect_type)

            for row in range(10):
                if row % 2 == 0:  # Четные ряды - слева направо
                    col_range = range(10)
                else:  # Нечетные ряды - справа налево
                    col_range = range(9, -1, -1)

                for col in col_range:
                    # Определение JSON-координат (vert, hor) с учётом зеркалирования
                    json_col = col if row % 2 == 0 else 9 - col
                    key = (row, json_col)

                    if key in defects and defects[key] != "good":
                        x, y = positions[row][col]
                        defect_positions.append((x, y, row, col, defects[key]))
                        print(
                            f"Дефект добавлен: [{row},{col}] (JSON [{
                            row},{json_col}]) тип={defects[key]}")

            print(f"\nВсего дефектов для обработки: {len(defect_positions)}")

            # --- Проход только по дефектным позициям ---
            for idx, (x, y, row, col, defect_type) in enumerate(defect_positions):
                print(
                    f"\n--- Обработка дефекта {idx+1}/{
                    len(defect_positions)}: [{row},{col}] тип={defect_type} ---")

                # Перемещение к ячейке (на высоте start_z)
                send_command(
                    serial_connection, f"G00 X{x:.3f} Y{y:.3f} Z{start_z:.3f} F{feed_rate}")

                # Опускание для захвата
                send_command(
                    serial_connection, f"G00 X{x:.3f} Y{y:.3f} Z{pickup_z:.3f} F{feed_rate}")

                # Включение вакуума
                send_command(serial_connection, "M106 S255")
                time.sleep(0.8)

                # Подъём с деталью
                send_command(
                    serial_connection, f"G00 X{x:.3f} Y{y:.3f} Z{start_z:.3f} F{feed_rate}")

                # Перемещение к зоне сброса (стартовая позиция)
                send_command(
                    serial_connection, f"G00 X{defect_x:.3f} Y{
                    defect_y_starter:.3f} Z{start_z:.3f} F{feed_rate}")

                # Опускание на нижнюю позицию для сброса
                send_command(
                    serial_connection, f"G00 X{defect_x:.3f} Y{
                    defect_y_starter:.3f} Z{defect_z_lower:.3f} F{feed_rate}")

                # Задержка (зависит от номера ряда)
                time.sleep(7.0 / (10 - row))

                # Движение к конечной точке сброса
                send_command(
                    serial_connection, f"G00 X{defect_x:.3f} Y{
                    defect_y:.3f} Z{defect_z_lower:.3f} F{feed_rate}")

                # Отключение вакуума
                send_command(
                    serial_connection, "M107")

                # Подъём наверх
                send_command(
                    serial_connection, f"G00 X{defect_x:.3f} Y{
                    defect_y:.3f} Z{defect_z_upper:.3f} F{feed_rate}")

                # Если это не последний дефект, перемещаемся к следующему
                if idx < len(defect_positions) - 1:
                    next_x, next_y, _, _, _ = defect_positions[idx + 1]
                    send_command(
                        serial_connection, f"G00 X{next_x:.3f} Y{
                        next_y:.3f} Z{start_z:.3f} F{feed_rate}")
                    # Задержка после перемещения
                    time.sleep(7.5 / (10 - row))

            # Возврат в домашнюю позицию после обработки всех дефектов
            send_command(serial_connection, "G28")
            serial_connection.close()

        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            enable_button()

    def disable_button():
        start_layout_button.disabled = True
        start_layout_button.style = ft.ButtonStyle(
            color=application_colors["unclickable"],
            bgcolor=application_colors["top_bar"],
            padding=20,
        )
        start_layout_button.update()

    def enable_button():
        start_layout_button.disabled = False
        start_layout_button.style = ft.ButtonStyle(
            color=application_colors["text"],
            bgcolor=application_colors["active"],
            padding=20,
        )
        start_layout_button.update()

    def start_clicked(_e):
        disable_button()
        threading.Thread(
            target=run_distribution,
            daemon=True
        ).start()

    start_layout_button.on_click = start_clicked

    controls_block = ft.Column(
        controls=[
            file_protocol_field,
            ft.Container(height=16),
            select_file_button,
            ft.Container(height=32),
            start_layout_button
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    return ft.Tab(
        text="Раскладчик",
        content=ft.Column(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            file_picker,
                            ft.Container(height=32),
                            ft.Row(
                                controls=[
                                    ft.Container(width=760),
                                    ft.Text(
                                        value="Управление раскладчиком",
                                        size=20,
                                        color=application_colors["text"],
                                        weight=ft.FontWeight.BOLD
                                    ),
                                    ft.Container(width=760)
                                ]
                            ),
                            ft.Container(height=32),
                            ft.Row(
                                controls=[controls_block],
                                alignment=ft.MainAxisAlignment.CENTER
                            ),
                            ft.Container(height=32)
                        ]
                    ),
                    padding=20,
                    border=ft.border.all(3),
                    border_radius=ft.border_radius.all(10),
                    width=1900,
                    margin=ft.margin.only(left=20, top=20, right=20, bottom=10)
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )
