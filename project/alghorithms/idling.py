import flet as ft
import time

from project.alghorithms.protocols import adding_to_protocol
from project.application.addition.colors import color_mode
from project.application.addition.snake_buttons import change_snake_button_color
from project.station.requests import move_to_coordinates
from project.configuration.worker import read_from_json, write_to_json
from project.station.connection import establish_connection, close_connection


def paint_cell(certain_number, snake_buttons,color):
    # Цветовая окраска проверяемой ячейки в зависимости от её годности
    val = read_from_json(
        'project/configuration/distances.json', 'distances_state')
    def change():
        if val == 0:
            change_snake_button_color(snake_buttons[certain_number-1], ft.colors.GREY)
        if val == 1:
            change_snake_button_color(snake_buttons[certain_number-1], color)
            if color == "#50af4c":
                adding_to_protocol(
                    (certain_number - 1) // 10, (certain_number - 1) % 10, "good")
            elif color == "#c89b00":
                adding_to_protocol(
                    (certain_number - 1) // 10, (certain_number - 1) % 10, "flatness")
            elif color == "#0096ff":
                adding_to_protocol(
                    (certain_number - 1) // 10, (certain_number - 1) % 10, "sinks")
            else:
                adding_to_protocol(
                    (certain_number - 1) // 10, (certain_number - 1) % 10, "glass")
        if val == 2:
            change_snake_button_color(snake_buttons[certain_number-1], ft.colors.GREEN)

    change()
    write_to_json('project/configuration/distances.json', 'distances_state', 0)


def coordinate_processing(x, y, certain_number):
    """
    Функция движения на ячейку по команде пользователя, реализовано в формате змейки.
    :param x:
    :param y:
    :param certain_number: номер ячейки
    :return: координаты движения
    """
    row_s = read_from_json("project/configuration/launch.json", "number_of_rows")
    col_s = read_from_json("project/configuration/launch.json", "number_of_columns")
    col = certain_number % col_s
    row = certain_number // row_s
    dx_unit = read_from_json(
        "project/configuration/launch.json", "distance_between_horizontal_centers")
    dy_unit = read_from_json(
        "project/configuration/launch.json", "distance_between_vertical_centers")

    if row % 2 == 0 :
        dx = col * dx_unit
        dy = row * dy_unit
        x += dx
        y -= dy
    else:
        dx = dx_unit * (certain_number % col_s - col_s + 1)
        dy = row * dy_unit
        x -= dx
        y -= dy
    return x,y


def movement_processing(certain_number, app_page, snake_buttons):
    """
    Перемещение робота на конкретную ячейку палеты и её проверка.

    :param app_page: Страница приложения для обновления цвета
                     ячейки в зависимости от результата проверки
    :param certain_number: Номер ячейки, на которую осуществляется перемещение
    :return: None
    """
    write_to_json("project/configuration/distances.json","certain_number", certain_number + 1)
    write_to_json("project/configuration/distances.json", "distances_state", 0)

    application_colors = color_mode()
    connection = establish_connection(app_page)

    if connection is not None:
        x = read_from_json(
            "project/configuration/coordinates.json", "x_coordinate_of_the_first_cell")
        y = read_from_json(
            "project/configuration/coordinates.json", "y_coordinate_of_the_first_cell")
        z = read_from_json(
            "project/configuration/coordinates.json", "z_coordinate_of_the_first_cell")

        x,y = coordinate_processing(x,y,certain_number)

        app_page.snack_bar = ft.SnackBar(
            content=ft.Text(
                f"Робот выдвинулся на ячейку {certain_number+1}. "
                f"Если сделан некорректный снимок, пожалуйста, "
                f"нажмите на ячейку вновь после остановки робота.",
                font_family="Montserrat",
                size=20,
                weight=ft.FontWeight.W_600,
                color=application_colors["text"]
            ),
            bgcolor=application_colors["red"],
            duration=4000
        )

        app_page.snack_bar.open = True
        move_to_coordinates(connection, x, y, z)
        btn_col = snake_buttons[certain_number].bgcolor
        if btn_col is None or btn_col == application_colors["inactive"] :
            change_snake_button_color(snake_buttons[certain_number], ft.colors.GREY)

        # Окраска ячейки в серый во время движения, без обращения к основной функции покраски
        write_to_json("project/configuration/position.json", "condition", 0)
        write_to_json("project/station/statuses.json", "moved_to_cell", 1)
        write_to_json("project/station/statuses.json", "right_view_waiting", 1)
        write_to_json("project/station/statuses.json", "start_showing", 1)
        write_to_json("project/configuration/position.json", "condition", 1)
        time.sleep(0.5)
        write_to_json("project/station/statuses.json", "moved_to_cell", 0)
        time.sleep(0.5)
        close_connection(connection)
    elif connection is None:
        return 0

    return 0
