import json
import openpyxl
from openpyxl.chart.reference import Reference
import win32com.client as win32
import os
from math import sqrt
from datetime import datetime
from flet import *
from flet import LineChart, LineChartData, LineChartDataPoint, FilePickerResultEvent, Page

from project.alghorithms.excel_processing import excel_processing
from project.application.addition.colors import color_mode
from project.application.addition.password_message import show_password_message
from project.configuration.worker import read_json_to_list, read_from_json


def count_stats(y_values):
    """
    Функция расчёта параметров и построения контрольных карт средних
    значений и размахов измеренных параметров. Данные поступают из
    JSON, заполненного во время проверки корпусов.

    :param y_values: Массив данных List[List[float]] для анализа
    :return: List[flet.Container, flet.Container] - контейнеры с построенными контрольными картами
    """
    # Цвета приложения
    application_colors = color_mode()

    # Массивы для промежуточных значений
    y_values_mean = []
    y_values_reach = []

    # Параметры условий выборки
    a2, d2, d3, d4 = 0.419, 2.704, 0.076, 1.924

    upper_line = 1.33
    lower_line = 1.17

    # Данные-заглушки на случай повреждения JSON
    if y_values is None or len(y_values) == 0 or len(y_values[0]) == 0:
        y_values = [
            [1.35, 1.19, 1.302, 1.236, 1.27, 1.254, 1.334],
            [1.205, 1.206, 1.238, 1.206, 1.238, 1.206, 1.222],
            [1.206, 1.334, 1.158, 1.206, 1.222, 1.222, 1.206]
        ]

    # Ход расчёта статистических параметров
    for point in y_values:
        if len(point) > 0:
            y_values_mean.append(sum(point) / len(point))
            y_values_reach.append(max(point) / min(point))

    x_central = x_central_filtered = round(sum(y_values_mean) / len(y_values_mean), 2)
    r_central = r_central_filtered = round(sum(y_values_reach) / len(y_values_reach), 2)

    x_upper = x_upper_filtered = round(x_central + r_central * a2, 2)
    x_lower = x_lower_filtered = round(x_central - r_central * a2, 2)
    r_upper = r_upper_filtered = round(r_central * d4 - 1, 2)
    r_lower = r_lower_filtered = round(r_central * d3, 2)

    summa = 0

    for k in range(len(y_values)):
        for n in range(len(y_values[k])):
            summa += pow((y_values[k][n] - x_central), 2)

    standard_deviation = standard_deviation_filtered = (
        sqrt((1 / ((len(y_values) * len(y_values_mean)) - 1)) * summa))
    filtered_x, filtered_r = 0, 0
    y_values_mean_filtered, y_values_reach_filtered = y_values_mean, y_values_reach
    # while True:
    #     y_values_mean_filtered, y_values_reach_filtered = zip(
    #         *[
    #             (mean, reach)
    #             for mean, reach in zip(y_values_mean, y_values_reach)
    #             if x_lower <= mean <= x_upper and r_lower <= reach <= r_upper
    #         ]
    #     )
    #
    #     y_values_mean_filtered = list(y_values_mean_filtered)
    #     y_values_reach_filtered = list(y_values_reach_filtered)
    #     if len(y_values_mean_filtered) == filtered_x and
    #     len(y_values_reach_filtered) == filtered_r:
    #         break
    #     filtered_x, filtered_r = len(y_values_mean_filtered), len(y_values_reach_filtered)
    #     x_central_filtered = round(sum(y_values_mean_filtered) / len(y_values_mean_filtered), 2)
    #     r_central_filtered = round(sum(y_values_reach_filtered) / len(y_values_reach_filtered), 2)
    #
    #     x_upper_filtered = round(x_central_filtered + r_central_filtered * a2, 2)
    #     x_lower_filtered = round(x_central_filtered - r_central_filtered * a2, 2)
    #     r_upper_filtered = round(r_central_filtered * d4 - 1, 2)
    #     r_lower_filtered = round(r_central_filtered * d3, 2)
    #     standard_deviation_filtered = r_central_filtered / d2

    # Индекс воспроизводимости процесса (или показатель возможностей процесса) Ср
    # связывает изменчивость реального процесса (его размах) с полем допуска,
    # установленным потребителем, например, в техническом задании.
    # Должен быть в диапазоне от 1 до 2, желательно не менее 1.33, идеально 2

    c_p = (upper_line - x_lower_filtered) / (
            6 * standard_deviation_filtered)  # тут надо заменить на допуски в мм

    # Cp используется с модифицированным индексом возможностей
    # процесса Cpk, описывающим возможности нецентрированного процесса
    # т.е. учитывающим смещение распределения относительно центрального значения:

    c_pk = min((upper_line - x_central_filtered) / (3 * standard_deviation_filtered),
               (x_central_filtered - lower_line) / (3 * standard_deviation_filtered))

    # для определения возможностей нестабильных процессов рекомендует,
    # наряду с индексами воспроизводимости Ср, Срk, использовать индексы пригодности Pр, Pрk

    p_p = (upper_line - lower_line) / (6 * standard_deviation)

    p_pk = min((upper_line - x_central_filtered) / (3 * standard_deviation),
               (x_central_filtered - lower_line) / (3 * standard_deviation))

    # Индексом стабильности процесса Рs называют отношение
    # индекса пригодности к индексу воспроизводимости, или отношение
    # оценки собственной изменчивости к оценке полной изменчивости процесса

    p_s = p_p / c_p

    # Индекс дрейфа центра группирования выборочной изменчивости
    # процесса Pd оценивают как отношение максимальной
    # разности средних арифметических двух выборок к допуску:

    p_d = (max(y_values_mean_filtered) - min(y_values_mean_filtered)) / (upper_line - lower_line)

    max_point = 0
    for i, point in enumerate(y_values_mean_filtered, 0):
        if i + 1 >= len(y_values_mean_filtered):
            break
        if abs(y_values_mean_filtered[i] - y_values_mean_filtered[i + 1]) > max_point:
            max_point = abs(y_values_mean_filtered[i] - y_values_mean_filtered[i + 1])

    # В качестве индекса нелинейности смещения центра
    # группирования выборочной изменчивости процесса Pn
    # (как частный случай предыдущего показателя Pd) принимают
    # отношение максимальной разности средних арифметических
    # двух соседних (последовательных) выборок к допуску:

    p_n = max_point / (upper_line - lower_line)

    # В качестве индекса динамики рассеяния выборочной
    # изменчивости процесса PdR используют отношение максимальной
    # разности статистических оценок рассеяния двух выборок
    # к значению наибольшей меры рассеяния этих выборок:
    p_dr = ((max(y_values_reach_filtered) - min(y_values_reach_filtered))
            / max(y_values_reach_filtered))

    max_point = 0
    r_i = 0

    for i, point in enumerate(y_values_reach_filtered, 0):
        if i + 1 >= len(y_values_reach_filtered):
            break
        if abs(y_values_reach_filtered[i] - y_values_reach_filtered[i + 1]) > max_point:
            max_point = abs(y_values_reach_filtered[i] - y_values_reach_filtered[i + 1])
            r_i = y_values_reach_filtered[i]

    # Под индексом нестабильности рассеяния выборочной изменчивости
    # процесса PnR понимают отношение максимальной разности размахов
    # двух соседних выборок к большему значению размаха этих выборок:
    p_nr = max_point / r_i

    # Под индексом максимального рассеяния PmR, или индексом наибольшего рассеяния выборочной
    # изменчивости понимают отношение максимального размаха выборки к допуску
    p_mr = max(y_values_reach_filtered) / (upper_line - lower_line)

    if (len(y_values_mean_filtered) < len(y_values_mean) / 2
            or len(y_values_reach_filtered) < len(y_values_reach) / 2):
        print("Выборка не представительна, больше половины выбросов")
        return


    # Сохранение точек графика в JSON для дальнейшей передачи в Excel
    with open("project/configuration/graph.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    data["mean_points"] = []
    data["mean_points"].extend(y_values_mean_filtered)
    data["reach_points"] = []
    data["reach_points"].extend(y_values_reach_filtered)

    with open("project/configuration/graph.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    # print(y_values_mean_filtered)
    # print(y_values_reach_filtered)

    points_mean = [LineChartDataPoint(x, round(y, 3))
                   for x, y in enumerate(y_values_mean_filtered)]
    points_reach = [LineChartDataPoint(x, round(y, 3))
                    for x, y in enumerate(y_values_reach_filtered)]

    reach_min_y = min(y_values_reach_filtered + [r_lower_filtered]) * 0.9
    reach_max_y = max(y_values_reach_filtered + [r_upper_filtered]) * 1.1

    # Создание графика
    mean_chart = LineChart(
        data_series=[
            LineChartData(
                data_points=points_mean,
                color=application_colors["text"],
                point=True,
            ),
            LineChartData(
                data_points=[LineChartDataPoint(0, x_central_filtered),
                             LineChartDataPoint(len(points_mean) - 1, x_central_filtered)],
                color=application_colors["text"],
                selected_point=False
            ),
            LineChartData(
                data_points=[LineChartDataPoint(0, x_upper_filtered),
                             LineChartDataPoint(len(points_mean) - 1, x_upper_filtered)],
                color=application_colors["text"],
                dash_pattern=[5, 5],
                selected_point=False
            ),
            LineChartData(
                data_points=[LineChartDataPoint(0, x_lower_filtered),
                             LineChartDataPoint(len(points_mean) - 1, x_lower_filtered)],
                color=application_colors["text"],
                dash_pattern=[5, 5],
                selected_point=False,
                disabled=True
            )
        ],
        border=border.only(left=BorderSide(4, Colors.with_opacity(0.5, Colors.ON_SURFACE)),
                           bottom=BorderSide(4, Colors.with_opacity(0.5, Colors.ON_SURFACE)),
                           right=BorderSide(4, Colors.with_opacity(0.5, Colors.ON_SURFACE))
                           ),
        horizontal_grid_lines=ChartGridLines(
            interval=0.2, color=Colors.with_opacity(0.2, Colors.ON_SURFACE), width=1
        ),
        vertical_grid_lines=ChartGridLines(
            interval=0.2, color=Colors.with_opacity(0.2, Colors.ON_SURFACE), width=1
        ),
        left_axis=ChartAxis(
            labels=[
                ChartAxisLabel(
                    value=i / 2,
                    label=Text(
                        str(i / 2),
                        size=14,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]),
                ) for i in range(15)
            ],
            labels_size=30,
            labels_interval=0.5
        ),

        bottom_axis=ChartAxis(
            labels=[
                ChartAxisLabel(
                    value=points_mean.index(point),
                    label=Text(
                        str(points_mean.index(point) + 1),
                        size=10,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]),
                ) for point in points_mean
            ],
            labels_size=40,
            labels_interval=1
        ),
        width=900,
        height=325,
        max_y=x_upper * 1.1,
        min_y=x_lower * 0.9,
    )

    # Контейнер с контрольной картой средних значений
    mean_container = Container(
        content=Column(
            controls=[
                Text(
                    value="Контрольная карта средних значений X",
                    text_align=TextAlign.CENTER,
                    color=application_colors["text"],
                    weight=FontWeight.BOLD,
                    size=18
                ),
                Text(
                    value=f"UCLX={x_upper_filtered}, "
                          f"LCLX={x_lower_filtered}, "
                          f"X центральный = {x_central_filtered}",
                    text_align=TextAlign.CENTER,
                    color=application_colors["text"],
                    size=16
                ),
                mean_chart
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            spacing=15
        ),
    )

    reach_chart = LineChart(
        data_series=[
            LineChartData(
                data_points=points_reach,
                color=application_colors["text"],
                stroke_width=2,
                point=True,
            ),
            # Центральная линия
            LineChartData(
                data_points=[LineChartDataPoint(0, r_central_filtered),
                             LineChartDataPoint(len(points_reach)-1, r_central_filtered)],
                color=application_colors["text"],
                stroke_width=1.5,
                dash_pattern=[5, 5]
            ),
            # Верхняя контрольная граница
            LineChartData(
                data_points=[LineChartDataPoint(0, r_upper_filtered),
                             LineChartDataPoint(len(points_reach)-1, r_upper_filtered)],
                color=Colors.RED,
                stroke_width=1.5,
                dash_pattern=[5, 5]
            ),
            # Нижняя контрольная граница
            LineChartData(
                data_points=[LineChartDataPoint(0, r_lower_filtered),
                             LineChartDataPoint(len(points_reach)-1, r_lower_filtered)],
                color=Colors.RED,
                stroke_width=1.5,
                dash_pattern=[5, 5]
            )
        ],
        border=border.all(1, Colors.with_opacity(0.5, Colors.ON_SURFACE)),
        horizontal_grid_lines=ChartGridLines(
            interval=(reach_max_y - reach_min_y)/10,
            color=Colors.with_opacity(0.2, Colors.ON_SURFACE),
            width=1
        ),
        left_axis=ChartAxis(
            labels_size=40,
            labels_interval=(reach_max_y - reach_min_y)/5
        ),
        bottom_axis=ChartAxis(
            labels_size=40,
            labels_interval=1
        ),
        width=900,
        height=325,
        min_y=max(0, reach_min_y),  # Не допускаем отрицательных значений
        max_y=reach_max_y,
        interactive=True,
        expand=True
    )

    # Контейнер с контрольной картой размахов
    reach_container = Container(
        content=Column(
            controls=[
                Text(
                    value=f"Контрольная карта размаха R",
                    text_align=TextAlign.CENTER,
                    color=application_colors["text"],
                    weight=FontWeight.BOLD,
                    size=18
                ),
                Text(
                    value=f"UCLR={r_upper_filtered}, "
                          f"LCLR={r_lower_filtered}, "
                          f"R центральный = {r_central_filtered}",
                    text_align=TextAlign.CENTER,
                    color=application_colors["text"],
                    size=16
                ),
                reach_chart
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            spacing=15
        )
    )

    return [mean_container, reach_container]


def create_statistics_layer():
    """
    Функция-контроллер вкладки "Статистическая обработка партии".
    Работает с полученными из count_stats контролами,
    добавляя к ним органы управления и оборачивая во вкладку.

    :return: flet.Tab statistics_tab
    """
    application_colors = color_mode()

    batch_number = TextField(
        label="Номер проверяемой партии",
        value="2025МСКМ-122Ш",
        read_only=True,
        width=400,
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    total_schemes = TextField(
        label="Количество схем в партии",
        keyboard_type=KeyboardType.NUMBER,
        read_only=True,
        width=400,
        value=str(read_from_json("project/configuration/graph.json", "total_schemes")),
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    good_schemes = TextField(
        label="Количество годных схем в партии",
        keyboard_type=KeyboardType.NUMBER,
        read_only=True,
        width=400,
        value=str(read_from_json("project/configuration/graph.json", "good_schemes")),
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    defective_schemes = TextField(
        label="Количество бракованных схем в партии",
        keyboard_type=KeyboardType.NUMBER,
        read_only=True,
        width=400,
        value=str(read_from_json("project/configuration/graph.json", "bad_schemes")),
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    checked_schemes = TextField(
        label="Проверенные схемы в партии",
        multiline=True,
        read_only=True,
        width=400,
        value=str(read_from_json("project/configuration/graph.json", "checked_schemes")),
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    center_column = Column(
        controls=(
            Text(
                "Отчёт по проверке партии",
                size=20,
                weight=FontWeight.BOLD,
                text_align=TextAlign.CENTER,
                color=application_colors["text"]
            ),
            batch_number,
            Row(
                controls=[
                    total_schemes,
                    checked_schemes,
                ],
                alignment=MainAxisAlignment.CENTER
            ),
            Row(
                controls=[
                    good_schemes,
                    defective_schemes
                ],
                alignment=MainAxisAlignment.CENTER
            )
        ),
        spacing=20,
        horizontal_alignment=CrossAxisAlignment.CENTER
    )

    def update_defective():
        """
        Вспомогательная функция, обновляет значения в текстовых полях с
        информацией о количестве годных/бракованных изделий в партии.

        :return: None
        """
        try:
            total = int(total_schemes.value) if total_schemes.value else 0
            good = int(good_schemes.value) if good_schemes.value else 0

            if total < 0 or good < 0:
                raise ValueError
            if good > total:
                good_schemes.error_text = "Не может быть больше общего количества"
            else:
                good_schemes.error_text = None

        except ValueError:
            defective_schemes.value = ""
            if total_schemes.value and not total_schemes.value.isdigit():
                total_schemes.error_text = "Введите число"
            else:
                total_schemes.error_text = None
            if good_schemes.value and not good_schemes.value.isdigit():
                good_schemes.error_text = "Введите число"
            else:
                good_schemes.error_text = None

        total_schemes.update()
        good_schemes.update()
        defective_schemes.update()

    total_schemes.on_change = update_defective
    good_schemes.on_change = update_defective

    button_styles = [
        ButtonStyle(
            shape=RoundedRectangleBorder(radius=radius),
            overlay_color=application_colors["hover"],
            bgcolor=application_colors["inactive"],
            color=application_colors["text"],
            text_style=TextStyle(size=20, weight=FontWeight.BOLD),
            animation_duration=300
        ) for radius in [
            border_radius.only(12, 0, 12, 0),
            border_radius.only(0, 0, 0, 0),
            border_radius.only(0, 0, 0, 0),
            border_radius.only(0, 0, 0, 0),
            border_radius.only(0, 12, 0, 12)
        ]
    ]

    button_styles_inactive = [
        ButtonStyle(
            shape=RoundedRectangleBorder(radius=radius),
            bgcolor=application_colors["top_bar"],
            color=application_colors["unclickable"],
            text_style=TextStyle(size=20, weight=FontWeight.BOLD),
            animation_duration=300
        ) for radius in [
            border_radius.only(12, 0, 12, 0),
            border_radius.only(0, 0, 0, 0),
        ]
    ]

    y_vals = read_json_to_list("project/configuration/statistics.json")
    containers = count_stats(y_vals)
    mean_container = containers[0]
    reach_container = containers[1]

    def reset_fields(e):
        """
        Вспомогательная функция, очищающая значения текстовых полей с
        информацией о количестве годных/бракованных деталей в партии.

        :param e: Событие нажатия на кнопку
        :return: None
        """
        batch_number.value = "2025МСКМ-122Ш"
        total_schemes.value = "1000"
        good_schemes.value = "0"
        defective_schemes.value = "0"
        checked_schemes.value = "0"
        batch_number.error_text = None
        total_schemes.error_text = None
        good_schemes.error_text = None
        total_schemes.update()
        good_schemes.update()
        defective_schemes.update()
        checked_schemes.update()
        batch_number.update()

    def on_print_button_click(_e):
        excel_processing()

    async def on_change_button_click(_e):
        pword_ok = await show_password_message(_e)

        if pword_ok:
            batch_number.read_only = False
            total_schemes.read_only = False

            _e.page.controls[0].tabs[5].content.controls[1].\
                controls[1].disabled = False
            _e.page.controls[0].tabs[5].content.controls[1].\
                controls[1].style = button_styles[1]

            _e.page.controls[0].tabs[5].content.controls[1].\
                controls[0].disabled = True
            _e.page.controls[0].tabs[5].content.controls[1].\
                controls[0].style = button_styles_inactive[0]

        await _e.page.update_async()
        return None

    def on_save_button_click(_e):
        batch_number.read_only = True
        total_schemes.read_only = True

        _e.page.controls[0].tabs[5].content.controls[1].\
            controls[1].disabled = True
        _e.page.controls[0].tabs[5].content.controls[1].\
            controls[1].style = button_styles_inactive[1]

        _e.page.controls[0].tabs[5].content.controls[1].\
            controls[0].disabled = False
        _e.page.controls[0].tabs[5].content.controls[1].\
            controls[0].style = button_styles[0]

        _e.page.update()

    def on_save_report_button_click(_e):
        # Загрузка книги
        file_path = "project/assets/report.xlsx"
        wb = openpyxl.load_workbook(file_path)
        ws = wb["Report"]

        # Очистка данных
        for row in range(2, 62):
            ws[f'M{row}'] = None
            ws[f'O{row}'] = None

        # Загрузка статистических данных из JSON
        with open("project/configuration/graph.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        # Заполнение основных показателей
        ws['F6'] = data["total_schemes"]
        ws['F8'] = data["checked_schemes"]
        ws['F10'] = data["good_schemes"]
        ws['F12'] = data["bad_schemes"]

        # Заполнение данных графиков
        mean_points = data["mean_points"]
        reach_points = data["reach_points"]

        for row, value in enumerate(mean_points, start=2):
            ws[f'M{row}'] = float(value)

        for row, value in enumerate(reach_points, start=2):
            ws[f'O{row}'] = float(value)

        # Обновление графиков
        for i, chart in enumerate(ws._charts):
            if isinstance(chart, openpyxl.chart.LineChart):
                chart.series.clear()  # Очистка старых данных

                # Выбор столбца с данными
                data_col = 13 if i == 0 else 15

                # Добавление новых данных
                chart.add_data(Reference(ws, min_col=data_col, min_row=1, max_row=61), titles_from_data=True)
                chart.set_categories(Reference(ws, min_col=1, min_row=2, max_row=61))

                for series in chart.series:
                    series.smooth = False

        # Функция для обработки результата выбора файла
        def on_save_result(e: FilePickerResultEvent):
            if not e.path:
                e.page.snack_bar = SnackBar(Text("Сохранение отменено"))
                e.page.snack_bar.open = True
                e.page.update()
                return

            # Сохранение отчета
            wb.save(e.path)

            # Уведомление об успешном сохранении
            e.page.snack_bar = SnackBar(Text(f"Отчет сохранен: {e.path}"))
            e.page.snack_bar.open = True
            e.page.update()

            # Обработка для печати
            excel = win32.Dispatch('Excel.Application')
            excel.Visible = True
            try:
                _ = excel.Workbooks.Open(os.path.abspath(e.path))

            finally:
                pass

        # Создание и вызов диалога сохранения
        save_dialog = FilePicker(on_result=on_save_result)
        _e.page.overlay.append(save_dialog)
        _e.page.update()

        # Генерация имени файла с временной меткой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dialog.save_file(
            allowed_extensions=["xlsx"],
            file_name=f"Отчет_{timestamp}.xlsx"
        )

    return Tab(
        text="Статистика партии",
        content=Column(
            controls=[
                Container(
                    content=Column(
                        controls=[
                            center_column,
                            Container(height=64),
                            Row(
                                controls=[
                                    mean_container,
                                    reach_container
                                ],
                                vertical_alignment=CrossAxisAlignment.END
                            ),
                        ]
                    ),
                    padding=20,
                    border=border.all(3, application_colors["text"]),
                    border_radius=border_radius.all(10),
                    width=1900,
                    margin=margin.only(left=20, top=20, right=20, bottom=10),
                ),
                Row(
                    controls=[
                        ElevatedButton(
                            "Изменить",
                            style=button_styles[0],
                            width=196,
                            height=56,
                            on_click=on_change_button_click
                        ),
                        ElevatedButton(
                            "Сохранить",
                            style=button_styles_inactive[1],
                            width=196,
                            height=56,
                            disabled=True,
                            on_click=on_save_button_click
                        ),
                        ElevatedButton(
                            "Сохранить отчёт",
                            style=button_styles[2],
                            width=196,
                            height=56,
                            on_click=on_save_report_button_click
                        ),
                        ElevatedButton(
                            "Обнулить",
                            style=button_styles[3],
                            width=196,
                            height=56,
                            on_click=reset_fields
                        ),
                        ElevatedButton(
                            "Распечатать",
                            style=button_styles[4],
                            width=196,
                            height=56,
                            on_click=on_print_button_click
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER,
                    spacing=8
                )
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER
        ),
    )
