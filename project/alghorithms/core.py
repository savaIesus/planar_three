import json
import time
from flet import *

from project.alghorithms.protocols import protocol_initialisation, protocol_finalization
from project.application.addition.colors import color_mode
from project.station.requests import move_to_home, move_to_coordinates
from project.configuration.worker import write_to_json, read_from_json, read_json_to_list
from project.station.connection import establish_connection, close_connection
from project.application.addition.snake_buttons import change_snake_button_color, change_button_border
from project.application.layers.statistics import count_stats
from project.application.layers.quality_map import refresh_snake_buttons


def main_algorithm(app_page, snake_buttons):
    """
    Главный алгоритм проверки палеты. Последовательно продвигается по всем
    ячейкам палеты, измеряет их и делает заключение о годности каждой ячейки.

    :param app_page: Страница приложения для обновления цветов ячеек в зависимости от их годности
    :param snake_buttons: Массив кнопок, содержащий индексы и порядок следования ячеек
    :return: None
    """

    def wait_for_processing():
        """
        Вспомогательная функция, разрешающая захват изображения
        с камеры для дальнейшего обнаружения дефектов.
        :return: None
        """
        write_to_json("project/station/statuses.json",
                      "moved_to_cell",
                      1)
        time.sleep(0.4)
        write_to_json("project/station/statuses.json",
                      "right_view_waiting",
                      1)
        time.sleep(0.4)
        write_to_json("project/station/statuses.json",
                      "moved_to_cell",
                      0)

    # Текстовые поля во вкладке "Статистика", содержащие
    # информацию о количестве проверенных/годных/бракованных деталей
    text_fields = []

    # Файл, в который будет записываться статистика
    with open("project/configuration/statistics.json", "w", encoding="utf-8") as file:
        json.dump([], file, ensure_ascii=False, indent=4)

    # Установка соединения со станцией на время выполнения алгоритма.
    connection = establish_connection(app_page)

    if connection is not None:
        # В начале алгоритма годность всех ячеек обнуляется
        application_colors = color_mode()
        for button in snake_buttons:
            change_button_border(button)
            change_snake_button_color(button, application_colors["inactive"])

        write_to_json("project/configuration/position.json",
                      "condition", 0)
        write_to_json("project/station/statuses.json",
                      "start_showing", 1)
        # # Калибровка и перемещение станции на координаты первой ячейки
        #move_to_home(connection)
        move_to_coordinates(connection,
            read_from_json("project/configuration/coordinates.json",
            "x_coordinate_of_the_first_cell"),
            read_from_json("project/configuration/coordinates.json",
            "y_coordinate_of_the_first_cell"),
            read_from_json("project/configuration/coordinates.json",
            "z_coordinate_of_the_first_cell"))

        write_to_json("project/station/statuses.json", "moved_to_home", 1)
        time.sleep(0.3)
        write_to_json("project/station/statuses.json", "right_view_waiting", 1)
        time.sleep(0.3)
        write_to_json("project/station/statuses.json", "moved_to_home", 0)

        rows = int(read_from_json('project/configuration/launch.json', 'number_of_rows'))
        column = int(read_from_json('project/configuration/launch.json', "number_of_columns"))
        with open('project/configuration/quality_map.json', 'r') as f:
            quality_data = json.load(f)

        # Начало записи протокола
        protocol_initialisation()

        # Прохождение по всем ячейкам:
        t = k = 0 # был двойной цикл
        button_number = 0
        with open('project/configuration/quality_map.json', 'r') as f:
            quality_data = json.load(f)

        write_to_json("project/configuration/distances.json", "certain_number", 1)

        for i in range(rows):
            for j in range(column):
                write_to_json("project/configuration/distances.json", "distances_state", 0)
                if read_from_json("project/station/statuses.json", "stopped") == 0:
                    while read_from_json("project/station/statuses.json", "paused") != 0:
                        time.sleep(0.1)
                    if i % 2 == 0:
                        if i == 0 and j == 0:
                            write_to_json("project/configuration/distances.json", "certain_number",1)
                        elif i == 0:
                                write_to_json("project/configuration/distances.json", "certain_number", j+1)
                        else:
                            write_to_json("project/configuration/distances.json", "certain_number", (i * column) + j+1)
                    else:
                        position = (i * column) + j + 1
                        write_to_json("project/configuration/distances.json", "certain_number", position )

                    # text_fields[1].value = str(int(text_fields[1].value) + 1)
                    # text_fields[1].update()

                    # Цветовая окраска проверяемой ячейки в зависимости от её годности
                    distance_state = read_from_json(
                        "project/configuration/distances.json",
                        "distances_state")

                    if distance_state in (0, 3): # КОЛ-ВО ЦЕТОВ ДЕФФЕКТОВ
                        change_snake_button_color(snake_buttons[button_number], colors.GREY)
                        time.sleep(0.2)

                    """elif distance_state == 2:
                        if snake_buttons[button_number].bgcolor != application_colors["red"]:
                            change_snake_button_color(
                                snake_buttons[button_number],
                                application_colors["green"])
                            write_to_json(
                                "project/configuration/position.json",
                                "condition",
                                1)
                        quality_data[t][k][i][j] = 2
                    elif distance_state == 1:
                        change_snake_button_color(
                            snake_buttons[button_number],
                            application_colors["red"])
                        write_to_json(
                            "project/configuration/position.json",
                            "condition",
                            0)
                        quality_data[t][k][i][j] = 1"""

                    write_to_json("project/station/statuses.json", "start_showing",1)
                    while read_from_json("project/station/statuses.json", "right_view_waiting") == 1:
                        time.sleep(0.2)
                    while read_from_json("project/station/statuses.json", "paused") != 0:
                        time.sleep(0.1)
                    if read_from_json("project/station/statuses.json", "stopped") == 1:
                        break
                    if j < column - 1:
                        if i % 2 == 0:
                            move_to_coordinates(
                                connection,
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_x") +
                                read_from_json(
                                    "project/configuration/launch.json",
                                    "distance_between_horizontal_centers"),
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_y"),
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_z"))
                            wait_for_processing()
                        elif i % 2 == 1:
                            move_to_coordinates(
                                connection,
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_x") -
                                read_from_json(
                                    "project/configuration/launch.json",
                                    "distance_between_horizontal_centers"),
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_y"),
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_z"))
                            wait_for_processing()
                    elif j == column - 1:
                        if i < rows - 1:
                            move_to_coordinates(
                                connection,
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_x"),
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_y") -
                                read_from_json(
                                    "project/configuration/launch.json",
                                    "distance_between_vertical_centers"),
                                read_from_json(
                                    "project/configuration/coordinates.json",
                                    "current_coordinate_of_the_station_by_z"))
                            wait_for_processing()
                        else:
                            wait_for_processing()
                else:
                    break
                write_to_json("project/configuration/position.json", "condition", 1)
                button_number += 1

            if read_from_json("project/station/statuses.json", "stopped") == 1:
                break

        move_to_coordinates(connection,
                            read_from_json("project/configuration/coordinates.json",
                                           "x_coordinate_of_the_first_cell"),
                            read_from_json("project/configuration/coordinates.json",
                                           "y_coordinate_of_the_first_cell"),
                            read_from_json("project/configuration/coordinates.json",
                                           "z_coordinate_of_the_first_cell"))
        print('Алгоритм проверки выполнен')
        with open('project/configuration/quality_map.json', 'w') as f:
            json.dump(quality_data, f, indent=2)
        # refresh_snake_buttons(t, k)

        # Разрыв соединения со станцией после выполнения алгоритма.
        write_to_json(
            "project/station/statuses.json",
            "right_view_waiting",
            0)
        close_connection(connection)

    elif connection is None:
        return None

    # Расчёт статистики по итогам проверки палеты и
    # последующее обновление графиков во вкладке "Статистика"
    # write_to_json("project/configuration/graph.json", "total_schemes", int(text_fields[0].value))
    # write_to_json("project/configuration/graph.json", "checked_schemes", int(text_fields[1].value))
    # write_to_json("project/configuration/graph.json", "good_schemes", int(text_fields[2].value))
    # write_to_json("project/configuration/graph.json", "bad_schemes", int(text_fields[3].value))
    y_vals = read_json_to_list("project/configuration/statistics.json")
    controls = count_stats(y_vals)
    write_to_json(
        "project/station/statuses.json",
        "stopped",
        0)
    print("конец")
    # app_page.controls[0].tabs[7].content.controls[0].\
    #     content.controls[2].controls[0] = controls[0]
    # app_page.controls[0].tabs[7].content.controls[0].\
    #     content.controls[2].controls[1] = controls[1]
    # app_page.update()

    # Завершение протокола
    protocol_finalization()

    return None
