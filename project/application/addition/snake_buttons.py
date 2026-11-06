from flet import *
from project.application.addition.colors import color_mode

application_colors = color_mode()
def change_snake_button_color(snake_button, color):
    """
    Изменяет цвет указанного квадрата.

    Параметры:
    squares: Двумерный массив квадратов.
    X (int): Индекс строки.
    Y (int): Индекс столбца.
    Color: Новый цвет квадрата.

    Возвращает:
    NONE
    """

    snake_button.bgcolor = color
    snake_button.update()

def change_button_border(snake_button):
    snake_button.side = None
    snake_button.BorderSide = None
    snake_button.style = ButtonStyle(
        shape=RoundedRectangleBorder(radius=8),
        bgcolor=application_colors["inactive"],
        color=application_colors["text"],
        text_style=TextStyle(font_family="Montserrat", weight=FontWeight.W_500),
        side=BorderSide(
            width=2,
            color=application_colors["inactive"]
        )
    )


