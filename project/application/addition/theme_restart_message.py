from flet import *
from project.application.addition.colors import color_mode
from project.configuration.worker import read_from_json, write_to_json


def show_restart_message(title, message, page):
    """
    Отображает модальное диалоговое окно, где пользователь выбирает:
    перезагрузить приложение, чтобы поменять цветовую тему, или отменить действие.

    :param title: Заголовок сообщения
    :param message: Тело сообщения
    :param page: Страница приложения, поверх которой будет нарисовано окно
    :return: None
    """
    def close_dialog(e):
        """
        Вспомогательная функция, закрывающая диалоговое окно.
        :param e: Событие нажатия на кнопку "Отмена"
        :return: None
        """
        e.page.dialog.open = False
        e.page.update()

    def restart_app(e):
        """
        Вспомогательная функция, изменяющая цветовую тему, записанную в
        JSON и перезагружающая (спойлер - просто выключающая) приложение.
        :param e: Событие нажатия на кнопку "ОК"
        :return: None
        """
        if read_from_json(
                "project/configuration/launch.json",
                "theme") == "light":
            write_to_json(
                "project/configuration/launch.json",
                "theme",
                "dark")
        else:
            write_to_json(
                "project/configuration/launch.json",
                "theme",
                "light")

        close_dialog(e)
        e.page.window_destroy()

    application_colors = color_mode()

    restart_dialog = AlertDialog(
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
            Row(
                controls=[
                    TextButton(
                        content=Text(
                            "Отмена",
                            size=24,
                            font_family="Montserrat",
                            weight=FontWeight.W_600,
                            color=application_colors["background"]
                        ),
                        width=172,
                        height=48,
                        on_click=close_dialog,
                        style=ButtonStyle(
                            bgcolor=application_colors["inactive"],
                            color=application_colors["text"],
                            overlay_color=application_colors["hover"],
                            shape=RoundedRectangleBorder(radius=8)
                        )
                    ),
                    TextButton(
                        content=Text(
                            "ОК",
                            size=24,
                            font_family="Montserrat",
                            weight=FontWeight.W_600,
                            color=application_colors["background"]
                        ),
                        width=172,
                        height=48,
                        on_click=restart_app,
                        style=ButtonStyle(
                            bgcolor=application_colors["active"],
                            color=application_colors["text"],
                            overlay_color=application_colors["hover"],
                            shape=RoundedRectangleBorder(radius=8)
                        )
                    ),
                ],
                alignment=MainAxisAlignment.CENTER,
                spacing=20
            )
        ],
        modal=True,
        bgcolor=application_colors["background"]
    )

    # Добавление диалогового окна в приложение
    page.dialog = restart_dialog
    restart_dialog.open = True
    page.update()
