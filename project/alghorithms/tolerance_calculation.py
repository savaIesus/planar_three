import time
from project.configuration.worker import read_from_json, write_to_json, append_distances_to_json,\
    hex_color
from project.alghorithms.idling import paint_cell
from flet import colors


def process_distances(distances, target_value=75):
    """
    Обрабатывает массив расстояний и возвращает результат в зависимости от условий:
    - Если все числа точно равны target_value - возвращает "exact_match" и записывает 1 в JSON
    - Если все числа в пределах target_value ± tolerance -
      возвращает "within_tolerance" и записывает 2 в JSON
    - Если отклонение больше чем ±tolerance - записывает 3 в JSON
    - Если массив пустой - возвращает "out_of_range" и записывает 0 в JSON

    :param distances: список чисел (расстояний)
    :param target_value: целевое значение (по умолчанию 75)
    :return: строка с результатом ("exact_match", "within_tolerance", "out_of_range")
    """
    dst = []

    valid_distances = [f for f in distances if f is not None]
    for distance in valid_distances:
        dst.append(round(float(distance) / 62.2, 3))

    append_distances_to_json(
        "project/configuration/statistics.json",
        dst)

    # Если массив пустой, возвращаем "out_of_range" и записываем 0
    if not valid_distances:
        write_to_json(
            "project/configuration/distances.json",
            "distances_state",
            0)
        return "out_of_range"

    # Проверяем, находятся ли все числа в пределах допуска
    all_within_tolerance = all(
        target_value - 2 <= d <= target_value + 8
        for d in distances
    )

    if all_within_tolerance:
        write_to_json(
            "project/configuration/distances.json",
            "distances_state",
            1)
        return "within_tolerance"

    # Если мы попали сюда, значит есть отклонение больше чем ±tolerance
    write_to_json(
        "project/configuration/distances.json",
        "distances_state",
        3)
    return "out_of_range"

def cell_color_change(obj_data: list, snake_buttons: list):
    certain_number = read_from_json('project/configuration/distances.json','certain_number')

    print(snake_buttons[certain_number-1].bgcolor, certain_number)
    cur_but_col = snake_buttons[certain_number - 1].bgcolor
    color_map = (colors.GREY, colors.GREEN)
    # случай когда пользователь заново нажмёт на проверенную ячейку и она проверится как годная
    # (или алгоритм не найдёт дефекта на выделенной камере)
    if obj_data:
        if ((cur_but_col in color_map) or (cur_but_col is None)) and not obj_data:
            write_to_json('project/configuration/distances.json', "distances_state", 1)
            paint_cell(certain_number, snake_buttons,None)
            write_to_json('project/configuration/distances.json', "distances_state", 0)
            return None

        for data in obj_data:
            if data[0]['color'] is not None:
                color = data[0]['color']
                color.reverse()
                write_to_json('project/configuration/distances.json', "distances_state", 1)
                paint_cell(certain_number, snake_buttons,hex_color(color))
                write_to_json('project/configuration/distances.json', "distances_state", 0)
    else:
        if cur_but_col is colors.GREY:
            write_to_json('project/configuration/distances.json', "distances_state", 1)
            paint_cell(certain_number, snake_buttons, hex_color([80,175,76]))
            write_to_json('project/configuration/distances.json', "distances_state", 0)


    write_to_json('project/configuration/distances.json', "distances_state", 0)
    return None

