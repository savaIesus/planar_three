import json
from flet import *
from project.configuration.worker import (read_from_json)
from project.application.addition.colors import color_mode


nested_snake_buttons = []

rows_file = int(read_from_json('project/configuration/launch.json','number_of_rows'))
column_file = int(read_from_json('project/configuration/launch.json',"number_of_columns"))

def refresh_snake_buttons(iter_i, iter_j):
    global nested_snake_buttons
    application_colors = color_mode()
    data_list = []

    with open('project/configuration/quality_map.json', 'r') as f:
        quality_data = json.load(f)

    for i in range(rows_file):
        for j in range(column_file):
            data_list.append(quality_data[iter_i][iter_j][i][j])

    for button in nested_snake_buttons[iter_i][iter_j]:
        button.style.bgcolor = (
            application_colors["inactive"] if data_list[int(button.text) - 1] == 0 else
            application_colors["red"] if data_list[int(button.text) - 1] == 1 else
            application_colors["green"]
        )

def create_quality_map_layer():
    """
    Функция, создающая вкладку проверки годности корпусов
    и подключающая все контролы, содержащиеся в ней,
    к обработчикам и событиям.
    :return: flet.Tab вкладка "Проверка годности корпусов"
    """
    global nested_snake_buttons
    # Чтение файла
    with open('project/configuration/quality_map.json', 'r') as f:
        quality_data = json.load(f)

    application_colors = color_mode()
    nested_snake_buttons = [[[] for _ in range(rows_file)] for _ in range(column_file)]

    def button_click(_e):
        """
        Обрабатывает событие нажатия на одну из кнопок, обозначающих элементы палеты.
        Допускает, чтобы только одна кнопка была "активной",
        все остальные циклично делаются неактивными за счёт
        итерации по snake_buttons.

        :param _e: событие нажатия
        :return: None
        """
        global nested_snake_buttons

        for i in range(rows_file):
            for j in range(column_file):
                for button in nested_snake_buttons[i][j]:
                    button.style = ButtonStyle(
                        shape=RoundedRectangleBorder(radius=8),
                        bgcolor=button.style.bgcolor,
                        color=application_colors["text"],
                        text_style=TextStyle(
                            font_family="Montserrat",
                            weight=FontWeight.W_500),
                            side=BorderSide(
                            width=5,
                            color=application_colors["inactive"]
                        )
                    )

        _e.control.style = ButtonStyle(
            shape=RoundedRectangleBorder(radius=8),
            bgcolor=_e.control.style.bgcolor,
            color=application_colors["text"],
            text_style=TextStyle(font_family="Montserrat", weight=FontWeight.W_500),
            side=BorderSide(
                width=5,
                color=application_colors["active"]
            )
        )

        _e.page.update()

    def generate_snake_buttons(rows, cols, iter_i, iter_j):
        """
        Генерирует матрицу кнопок, визуализирующих элементы палеты, и объединяет их в ряды.
        Для синхронизации также добавляет сами кнопки в список snake_buttons.

        :param rows: количество кнопок по вертикали
        :param cols: количество кнопок по горизонтали
        :return: List[Row[ElevatedButton, ...], ...]
        """
        global nested_snake_buttons
        nested_snake_buttons[iter_i][iter_j].clear()

        buttons = []
        for i in range(rows):
            row = [
                ElevatedButton(
                    text=str(i * cols + j + 1),
                    on_click=button_click,
                    width=38,
                    height=30,

                    style=ButtonStyle(
                        shape=RoundedRectangleBorder(radius=8),
                        bgcolor=(
                            application_colors["inactive"] if quality_data[iter_i][iter_j][i][j] == 0 else
                            application_colors["red"] if quality_data[iter_i][iter_j][i][j] == 1 else
                            application_colors["green"]
                        ),
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
                nested_snake_buttons[iter_i][iter_j].append(button)
            if i % 2 == 1:
                row.reverse()
            buttons.append(Row(controls=row, spacing=5))

        # return buttons[::-1]
        return buttons

    # Создаем сетку 5×5, где каждый элемент — это сетка 6×5 кнопок
    grid_of_grids = []
    for j in range(1):  # 5 строк в большой сетке
        row_of_grids = []
        for i in range(1):  # 5 столбцов в большой сетке
            r = rows_file
            c = column_file
            # Создаем сетку 6×5 кнопок и добавляем в строку
            button_grid = Column(
                controls=generate_snake_buttons(rows=r,cols=c, iter_j=j, iter_i=i),  # Каждая под-сетка 6×5
                spacing=5,
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER
            )
            row_of_grids.append(button_grid)
        # Добавляем строку из 5 под-сеток в общую сетку
        grid_of_grids.append(Row(controls=row_of_grids, spacing=48))

    # Итоговый контейнер — это Column из Row с под-сетками
    final_grid = Column(
        controls=grid_of_grids,
        spacing=16,
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER
    )

    matrix_column = Column(
        controls=[
            final_grid,
        ],
        alignment=MainAxisAlignment.CENTER,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    quality_map_tab = Tab(
        text="Карта годности",
        content=Container(
            content=Column(
                controls=[
                    Row(
                        controls=[
                            Container(expand=True),
                            matrix_column,
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

    return quality_map_tab
