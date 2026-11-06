import asyncio, os
import json

from PIL.ImageOps import expand
from flet import *

from project.configuration.worker import read_from_json, hex_color, shorten_path, copy_file
from project.application.addition.colors import color_mode

path = r'project\station\weights\models_new.json'
far = 'far'
middle = 'middle'
near = 'near'

def update_model_data(cam_name: str, model_key: str, new_data: dict):
    """
    Функция обновления данных в json с информацией о моделях
    :param cam_name: - имя текущей камеры
    :param model_key: - id модели по выбранной камере
    :param new_data: - обновлённая информация которая будет в json
    :return:
    """
    full_data = read_from_json(path, cam_name)
    if model_key in full_data:
        full_data[model_key].update(new_data)

    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    data[cam_name] = full_data
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def new_model_data(cam_name: str, new_data: dict):
    """
    Добавление новой модели нейросети
    :param cam_name: - имя текущей камеры
    :param new_data: - данные для текущей камеры
    :return: - None
    """
    # Считываем весь JSON по опр. камере
    with open(path, 'r', encoding='utf-8') as file:
        full_data = json.load(file)

    if cam_name not in full_data:
        print('Ошибка названия камеры, add')

    num = str(len(full_data[cam_name]) + 1)
    full_data[cam_name][num] = new_data
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(full_data, file, indent=4, ensure_ascii=False)


def delete_model_data(key, cam_name):
    """
    Удаление данных с выбранного id по названию камеры,
    после перезапись данных всей камеры чтобы не слетели id
    :param key: - id камеры по выбранному названию
    :param cam_name: - название камеры
    :return: - None
    """
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    cam_data = data[cam_name]
    del cam_data[key]
    temp_data = list(cam_data.values())
    cam_data = {}

    for num, dt in enumerate(temp_data):
        cam_data[f'{num + 1}'] = dt

    data[cam_name] = cam_data
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)


async def show_edit_dialog(e, model_data, on_save_callback, type_flag):
    """
    Показывает диалог с параметрами выбранной нейросети
    :param e: - событийный параметр flet
    :param model_data: - старые данные о изменяемом пункте
    :param on_save_callback: - функция-коллбэк для обновления информации в json
    :param type_flag: - флаг на 2 случая - при создании нового и изменения старого
    :return: None
    """
    application_colors = color_mode()
    pick_path = ''

    def styled_text_field(label, value="", **kwargs):
        return TextField(
            label=label,
            value=value,
            color=application_colors["text"],
            border_color=application_colors["text"],
            label_style=TextStyle(color=application_colors["text"]),
            **kwargs
        )

    name_field = styled_text_field("Название", model_data["name"])
    description_field = styled_text_field("Описание", model_data["description"], multiline=True, max_lines=10)
    conf_field = styled_text_field("Увр-ность", model_data["conf"], expand=True)

    color_field_r = styled_text_field("Red", str(model_data["color"][0]), expand=True)
    color_field_g = styled_text_field("Green", str(model_data["color"][1]), expand=True)
    color_field_b = styled_text_field("Blue", str(model_data["color"][2]), expand=True)
    path_field = styled_text_field("Путь к модели нейросети", model_data["path"],
                                   read_only = True, expand=True, multiline=True, max_lines=3)
    color_box = Container(width=25, height=25, bgcolor=hex_color(model_data['color']),
                          border_radius=4,margin = margin.only(left=6,right=7))
    file_picker = FilePicker()

    if type_flag == 'add':
        # второй случай при добавлении новой нейросети в список
        for i in [
            name_field, description_field,
            color_field_g, color_field_b,
            color_field_r, path_field,conf_field]:
            i.value = ''
        color_box.bgcolor = hex_color([0, 0, 0])

    def box_color_preview(_):
        """
        Функция обновления цветного квадрата в диалоговом окне
        :param _: - заглушка
        :return: - None
        """

        def safe_parse(val):
            try:
                return min(int(int(val)), 255)
            except ValueError:
                return 0

        r = safe_parse(color_field_r.value)
        g = safe_parse(color_field_g.value)
        b = safe_parse(color_field_b.value)

        color_box.bgcolor = hex_color([r, g, b])

        color_field_r.value = str(r)
        color_field_g.value = str(g)
        color_field_b.value = str(b)

        e.page.update()

    color_field_r.on_change = box_color_preview
    color_field_g.on_change = box_color_preview
    color_field_b.on_change = box_color_preview

    def pick_file_result(_e):
        def on_dialog_result(_e: FilePickerResultEvent):
            nonlocal pick_path
            print("Selected files:", _e.files)
            print("Selected file or directory:", _e.path)
            if _e.files[0].path is not None:
                pick_path = _e.files[0].path
                fin_dir = os.path.dirname(path) + r'\\' + _e.files[0].name
                path_field.value = shorten_path(fin_dir,4)
                _e.page.update()

                print(fin_dir)
            else:
                print('Путь не выбран')

        file_picker.on_result = on_dialog_result
        file_picker.pick_files(
            allow_multiple=False,
            allowed_extensions=["pt"]
        )


    async def apply_changes(_e):
        """
        Сохранение изменений в json
        :param _e: - событийный параметр flet
        :return:
        """
        updated_data = {
            "name": name_field.value,
            "description": description_field.value,
            "color": [
                int(color_field_r.value),
                int(color_field_g.value),
                int(color_field_b.value)
            ],
            "path": path_field.value,
            "conf": conf_field.value
        }

        dlg.open = False
        await e.page.update_async()
        copy_file(pick_path, os.path.dirname(path)) # копируем нейронку в папку weights
        # Сохраняем новые данные через callback
        on_save_callback(updated_data)

    choose_path_btn = IconButton(
        tooltip="Выберите файл",
        icon=icons.FOLDER_COPY_SHARP,
        icon_color=application_colors["text"],
        on_click=pick_file_result,
        icon_size=25,
        hover_color=application_colors['inactive']
    )
    dlg = AlertDialog(
        modal=True,
        title=Text("Редактировать нейросеть", size=20, color=application_colors['text']),
        content=Column(
            controls=[
                name_field,
                Row([description_field,conf_field]),
                Row([color_field_r, color_field_g, color_field_b, color_box]),
                Row([path_field, choose_path_btn,file_picker], spacing=7),
            ],
            tight=True,
            width=400,

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
                       on_click=lambda e: setattr(dlg, "open", False) or e.page.update(),
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


async def show_delete_dialog(_e, on_delete_callback):
    """
    Диалоговое окно на подтверждение удаления пункта
    :param _e: событийный параметр flet
    :param on_delete_callback: функция-коллбэк обновления данных в интерфейсе
    :return: None
    """
    application_colors = color_mode()

    async def delete_action(e):  # передаём событие в функцию-обработчик
        if on_delete_callback:
            delete_attention.open = False
            await e.page.update_async()
            await on_delete_callback()

    delete_attention = AlertDialog(
        title=Text(
            value='Вы точно хотите удалить нейросеть?',
            size=24,
            font_family="Montserrat",
            weight=FontWeight.W_600,
            color=application_colors["red"],
            text_align=TextAlign.CENTER,
            bgcolor=application_colors['top_bar'],

        ),
        actions=[
            TextButton(
                "Удалить", on_click=delete_action,
                style=ButtonStyle(
                    color=application_colors['text'],
                    overlay_color=application_colors["hover"]
                )
            ),
            TextButton("Отмена",
                       on_click=lambda e: setattr(delete_attention, "open", False) or e.page.update(),
                       style=ButtonStyle(
                           color=application_colors['text'],
                           overlay_color=application_colors["hover"]
                       ),
            )
        ],
        actions_alignment=MainAxisAlignment.END,
        bgcolor=application_colors['top_bar'],
    )
    _e.page.dialog = delete_attention
    delete_attention.open = True

    await _e.page.update_async()
