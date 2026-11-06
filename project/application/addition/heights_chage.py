import asyncio
import json

from flet import *
from project.application.addition.colors import color_mode
from project.application.addition import error_message

path = r'project\configuration\heights_cfg.json'
def update_height_data(new_data: dict):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(new_data, file, indent=4, ensure_ascii=False)



async def show_edit_heights_dialog(e, model_data, on_save_callback):
    """
    :param e:
    :param model_data:
    :param on_save_callback:
    :return:
    """
    application_colors = color_mode()
    print(model_data)
    def styled_text_field(label, value="", **kwargs):
        return TextField(
            label=label,
            value=value,
            color=application_colors["text"],
            border_color=application_colors["text"],
            label_style=TextStyle(color=application_colors["text"]),
            **kwargs
        )

    max_field = styled_text_field("Максимально возможная высота", model_data["max"], expand=True)
    min_field = styled_text_field("Минимально возможная высота", model_data["min"],expand=True)
    average_field = styled_text_field("Максимальная разница между высотами окна", model_data["avg"], expand=True)

    async def apply_changes(_e):
        """
        :param _e:
        """
        updated_data = model_data
        try:
            updated_data = {
                "max": int(max_field.value),
                "min": int(min_field.value),
                "avg": int(average_field.value)
            }
        except ValueError:
            error_message.show_error(
                'Ошибка типа вводимых данных',
                'Вводите только целочисленные значения',
                _e.page
            )
            setattr(dlg, "open", False)
            await _e.page.update_async()

        dlg.open = False
        await e.page.update_async()

        # Сохраняем новые данные через callback
        on_save_callback(updated_data)


    dlg = AlertDialog(
        modal=True,
        title=Text("Изменить предельные значения измерение разновысотности",
                   size=20, color=application_colors['text']
                   ),
        content=Column(
            controls=[
                Row([average_field]),
                Row([max_field, min_field]),
            ],
            tight=True,

        ),
        actions=[
            TextButton(
                "Сохранить",
                on_click=apply_changes,
                style=ButtonStyle(
                    color=application_colors['text'],
                    overlay_color=application_colors["hover"]
                ),
            ),
            TextButton("Отмена",
                       on_click=lambda _e: setattr(dlg, "open", False) or e.page.update(),
                       style=ButtonStyle(
                           color=application_colors['text'],
                           overlay_color=application_colors["hover"]
                       ),
            ),
        ],
        actions_alignment=MainAxisAlignment.END,
        bgcolor=application_colors['top_bar'],
    )

    e.page.dialog = dlg
    dlg.open = True
    await e.page.update_async()

    # Ждём закрытия
    while dlg.open:
        await asyncio.sleep(0.1)

