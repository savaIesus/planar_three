from flet import *
from project.application.addition.colors import color_mode

def show_error(title, message, page):
    """
    Выводит на экран модальное диалоговое окно с сообщением об ошибке.

    :param title: Заголовок сообщения
    :param message: Тело сообщения
    :param page: Страница приложения, на которой будет нарисовано окно
    :return: None
    """
    def close_dialog(e):
        """
        Вспомогательная функция, закрывающая диалоговое окно.
        :param e: Событие нажатия на кнопку "ОК"
        :return: None
        """
        e.page.dialog.open = False  # Закрываем диалог
        e.page.update()  # Обновляем страницу

    application_colors = color_mode()

    error_dialog = AlertDialog(
        title=Text(
            title,
            size=24,
            font_family="Montserrat",
            weight=FontWeight.W_600,
            color=application_colors["red"],
            text_align=TextAlign.CENTER
        ),
        content=Text(
            message,
            size=20,
            font_family="Montserrat",
            weight=FontWeight.W_400,
            color=application_colors["text"],
            text_align=TextAlign.CENTER
        ),
        actions=[
            Container(
                content=TextButton(
                    content=Text(
                        "Продолжить",
                        size=24,
                        font_family="Montserrat",
                        weight=FontWeight.W_600,
                        color=application_colors["background"]
                    ),
                    width=172,
                    height=48,
                    on_click=close_dialog,
                    style=ButtonStyle(
                        bgcolor=application_colors["active"],
                        color=application_colors["text"],
                        overlay_color=application_colors["hover"],
                        shape=RoundedRectangleBorder(radius=8)
                    )
                ),
                alignment=alignment.center
            )
        ],
        modal=True,
        bgcolor=application_colors["background"]
    )

    page.dialog = error_dialog
    error_dialog.open = True
    page.update()
