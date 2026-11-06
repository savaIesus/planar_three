from flet import *
from project.application.addition.colors import color_mode


def create_guide_layer():
    application_colors = color_mode()

    tab_content = Column(
        spacing=20,
        controls=[
            Container(height=4),
            Row(
                controls=[
                    Container(width=496),
                    Text(
                        "РУКОВОДСТВО ОПЕРАТОРА СИСТЕМЫ ОБНАРУЖЕНИЯ ДЕФЕКТОВ",
                        size=24,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                ]
            ),
            Container(height=4),
            Text(
                "Проверка годности изделия:",
                size=18,
                weight=FontWeight.BOLD,
                text_align=TextAlign.LEFT,
                color=application_colors["text"]
            ),
            Row(
                controls=[
                    Text(
                        "1. Для начала инспекции изделий нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Запуск\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        ". Ожидайте, пока все обозначения изделий на карте годности"
                        "не будут окрашены соответственно степени их годности.",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Row(
                controls=[
                    Text(
                        "Зелёный цвет",
                        size=15,
                        color=colors.GREEN,
                        weight=FontWeight.BOLD,
                    ),
                    Text(
                        "соответствует изделию, в точности соответствующему техническим условиям.",
                        size=15,
                        color=application_colors["text"]
                    ),
                ],
                spacing=4,
                alignment=MainAxisAlignment.START,
            ),
            Row(
                controls=[
                    Text(
                        "Любой иной цвет",
                        size=15,
                        color=colors.RED,
                        weight=FontWeight.BOLD,
                    ),
                    Text(
                        "соответствует изделию, не являющемуся годным.",
                        size=15,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
            ),
            Row(
                controls=[
                    Text(
                        "2. Для приостановки инспекции нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Пауза\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        " и дождитесь остановки движения микроскопа.",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Row(
                controls=[
                    Text(
                        "3. Для возобновления работы нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Продолжить\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        ", убедившись, что микроскоп остановился.",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Row(
                controls=[
                    Text(
                        "4. Для полной остановки инспекции нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Стоп\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        " и дождитесь остановки движения микроскопа.",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Container(height=4),
            Text(
                "Калибровка первой ячейки:",
                size=18,
                weight=FontWeight.BOLD,
                text_align=TextAlign.LEFT,
                color=application_colors["text"]
            ),
            Row(
                controls=[
                    Text(
                        "1. Для подключения изображения с камеры нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Подключить камеру\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        ".",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Row(
                controls=[
                    Text(
                        "2. Для изменения координат нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Изменить координаты\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        " и выберите значение шага одной из клавиш в меню ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Шаг\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        ".",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Text(
                "3. Используя клавиши с пиктограммами стрелок,"
                "установите нужные координаты первой ячейки так, чтобы "
                "в окне камеры были видны 8 контактов, а расстояние от края окна"
                "до крайних слева и справа контактов было одинаковым.",
                size=15,
                text_align=TextAlign.LEFT,
                color=application_colors["text"]
            ),
            Text(
                "Крестовидная система стрелок слева управляет движением"
                "микроскопа вдоль паллеты по вертикали и горизонтали.",
                size=15,
                text_align=TextAlign.LEFT,
                color=application_colors["text"]
            ),
            Text(
                "Вертикальная система стрелок справа управляет"
                "удалением/приближением микроскопа к паллете.",
                size=15,
                text_align=TextAlign.LEFT,
                color=application_colors["text"]
            ),
            Row(
                controls=[
                    Text(
                        "Клавиша ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"⌂ Все\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        " обозначает возвращение микроскопа на нулевые координаты.",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Row(
                controls=[
                    Text(
                        "4. Координатные оси показывают текущее положение микроскопа",
                        size=15,
                        color=application_colors["text"],
                    ),
                    Text(
                        "(светлая точка)",
                        size=15,
                        color=application_colors["active"],
                        weight=FontWeight.BOLD,
                    ),
                    Text(
                        "в пространстве относительно ранее сохранённых координат",
                        size=15,
                        color=application_colors["text"],
                    ),
                    Text(
                        "(тёмная точка)",
                        size=15,
                        color=application_colors["text"],
                        weight=FontWeight.BOLD,
                    ),
                    Text(
                        ".",
                        size=15,
                        color=application_colors["text"],
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=4
            ),
            Row(
                controls=[
                    Text(
                        "5. Для сохранения выбранных координат после"
                        "завершения калибровки нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Сохранить координаты\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        ".",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
            Row(
                controls=[
                    Text(
                        "6. Для отключения изображения с камеры после"
                        "завершения калибровки нажмите клавишу ",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                    Text(
                        "\"Отключить камеру\"",
                        size=15,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"]
                    ),
                    Text(
                        ".",
                        size=15,
                        text_align=TextAlign.LEFT,
                        color=application_colors["text"]
                    ),
                ],
                alignment=MainAxisAlignment.START,
                wrap=True,
                spacing=0
            ),
        ],
    )

    guide_tab = Tab(
        text="Руководство оператора",
        content=Container(
            content=tab_content,
            padding=10,
        ),
    )

    return guide_tab
