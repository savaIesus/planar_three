import asyncio

from flet import *

from project.application.addition.colors import color_mode


async def show_password_message(_e) -> bool:
    correct_password = "3590"
    pword_ok = False

    application_colors = color_mode()

    # Поле для ввода пароля
    password_field = TextField(
        label="Введите пароль",
        text_size=24,
        bgcolor=application_colors["background"],
        password=True,
        can_reveal_password=True,
        width=368,
        height=96
    )

    async def close_dlg(_e):
        nonlocal pword_ok
        if password_field.value == correct_password:
            dlg.open = False
            _e.page.snack_bar = SnackBar(
                content=Text(
                    "Пароль верный! Доступ разрешён.",
                    font_family="Montserrat",
                    size=20,
                    weight=FontWeight.W_600,
                    color=application_colors["text"]
                ),
                bgcolor=Colors.GREEN_700,
                duration=1500
            )
            _e.page.snack_bar.open = True
            pword_ok = True
        else:
            _e.page.snack_bar = SnackBar(
                content=Text(
                    "Неверный пароль! Попробуйте снова.",
                    font_family="Montserrat",
                    size=20,
                    weight=FontWeight.W_600,
                    color=application_colors["text"]
                ),
                bgcolor=application_colors["red"],
                duration=1500
            )
            _e.page.snack_bar.open = True

        await _e.page.update_async()

    dlg = AlertDialog(
        modal=True,
        bgcolor=application_colors["background"],
        title=Text(
            "Введите пароль для изменения данных",
            size=24,
            font_family="Montserrat",
            weight=FontWeight.W_600,
            color=application_colors["red"],
            text_align=TextAlign.CENTER
        ),
        content=password_field,
        actions=[
            TextButton(
                content=Text(
                    "ОК",
                    size=24,
                    font_family="Montserrat",
                    weight=FontWeight.W_600,
                    color=application_colors["text"]
                ),
                width=172,
                height=48,
                on_click=close_dlg,
                style=ButtonStyle(
                    bgcolor=application_colors["active"],
                    color=application_colors["text"],
                    overlay_color=application_colors["hover"],
                    shape=RoundedRectangleBorder(radius=8)
                )
            ),
            TextButton(content=Text(
                        "Отмена",
                        size=24,
                        font_family="Montserrat",
                        weight=FontWeight.W_600,
                        color=application_colors["text"]
                    ),
                    width=172,
                    height=48,
                    on_click=lambda e: setattr(dlg, "open", False) or _e.page.update(),
                    style=ButtonStyle(
                        bgcolor=application_colors["inactive"],
                        color=application_colors["text"],
                        overlay_color=application_colors["hover"],
                        shape=RoundedRectangleBorder(radius=8)
                    )
            )
        ],
        actions_alignment=MainAxisAlignment.CENTER,
    )

    _e.page.dialog = dlg
    dlg.open = True
    await _e.page.update_async()

    while dlg.open:
        await asyncio.sleep(0.1)

    return pword_ok
