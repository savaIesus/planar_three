import json

from flet import *


from project.station.weights.networks_vault import middle, near, far
from project.application.addition.colors import color_mode
from project.application.addition.edit_dialog import show_edit_dialog, update_model_data, new_model_data, \
    show_delete_dialog, delete_model_data
from project.application.addition.heights_chage import show_edit_heights_dialog, update_height_data
from project.configuration.worker import read_from_json, hex_color
from project.station.weights.networks_vault import networks_init
import project.application.addition.info_page as infp
from project.application.addition.password_message import show_password_message

settings_file = "project/configuration/launch.json"

is_edit_mode = False

application_colors = color_mode()

default_active_button_style = ButtonStyle(
        shape=RoundedRectangleBorder(radius=10),
        overlay_color=application_colors["hover"],
        bgcolor=application_colors["inactive"],
        color=application_colors["text"],
        text_style=TextStyle(size=18, weight=FontWeight.BOLD),
        animation_duration=300,
    )

default_inactive_button_style = ButtonStyle(
    shape=RoundedRectangleBorder(radius=10),
    overlay_color=application_colors["hover"],
    bgcolor=application_colors["top_bar"],
    color=application_colors["unclickable"],
    text_style=TextStyle(size=18, weight=FontWeight.BOLD),
    animation_duration=300,
)

data_column_ref = Ref[Column]()
edit_mode_button_ref = Ref[ElevatedButton]()
save_button_ref = Ref[ElevatedButton]()
add_button_ref = Ref[IconButton]()
container_button_ref = Ref[IconButton]()
change_heights_ref = Ref[IconButton]()

def read_settings(key,  default=None):
    data = read_from_json(r'project\station\weights\models_new.json',key)
    if data is None:
        print('Ошибка пути к файлу с данными нейросетей')
    return data

async def change_information(_e):
    """
    Обновляет информацию о нейросетях на уровне программы,
    также обновляет информационную панель.
    :param _e: Событие нажатия на кнопку
    :return: None
    """
    global is_edit_mode
    pword_ok = True #  await show_password_message(_e)

    if pword_ok:
        is_edit_mode = True
        # Активируем все иконки
        for container in _e.page.controls[0].tabs[3].content.controls[1].content.controls:
            for neural_block in container.content.controls[1].controls[0].controls:
                for c in neural_block.content.controls[1].content.controls[2].content.controls:
                    c.icon_color = application_colors["text"]
                    c.disabled = False

            # Активируем кнопку добавления
            add_btn = container.content.controls[1].controls[1]
            add_btn.icon_color = application_colors["text"]
            add_btn.disabled = False

        # Отключаем кнопку "Изменить"
        edit_mode_button_ref.current.disabled = True
        edit_mode_button_ref.current.style = default_inactive_button_style

        # Активируем кнопку "Сохранить"
        save_button_ref.current.disabled = False
        save_button_ref.current.style = default_active_button_style

        # активируем кнопку изменения величины разновысотности
        change_heights_ref.current.disabled = False
        change_heights_ref.current.style = default_active_button_style

    await _e.page.update_async()

async def save_information(_e):
    """
    Обработчик нажатия на кнопку входа в режим изменения координат.
    :param _e: Событие нажатия на кнопку
    :return: None
    """
    global is_edit_mode
    is_edit_mode = False
    # Активируем все иконки
    for container in _e.page.controls[0].tabs[3].content.controls[1].content.controls:
        for neural_block in container.content.controls[1].controls[0].controls:
            for c in neural_block.content.controls[1].content.controls[2].content.controls:
                c.icon_color = application_colors["inactive"]
                c.disabled = True

        # Активируем кнопку добавления
        add_btn = container.content.controls[1].controls[1]
        add_btn.icon_color = application_colors["inactive"]
        add_btn.disabled = True

    edit_mode_button_ref.current.disabled = False
    edit_mode_button_ref.current.style = default_active_button_style

    change_heights_ref.current.disabled = True
    change_heights_ref.current.style = default_inactive_button_style

    save_button_ref.current.disabled = True
    save_button_ref.current.style = default_inactive_button_style

    networks_init()
    infp.info_page_update()
    await _e.page.update_async()


async def on_click_heights_edit(e):

    with open(r'project\configuration\heights_cfg.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    await show_edit_heights_dialog(
        e, data,
        lambda new_data: (
            update_height_data(new_data),
        ),
    )
def create_neural_networks_list():

    def refresh_data():
        data_column_ref.current.controls.clear()
        data_column_ref.current.controls.extend([
            background_create(far),
            background_create(middle),
            background_create(near),
        ])
        data_column_ref.current.update()


    def neural_container(cam_name, data):
        """
        Создание всех элементов в таблице по выбранной камере
        :param cam_name: - имя камеры
        :param data: - все данные из json
        :return: - спсок всех
        """
        containers = []

        for model_key, model_data in data.items():
            async def on_click_edit(e, model=model_data, key = model_key):
                """
                Функция изменения элемента таблицы c обновлением интерфейса
                :param e: - событийный параметр  flet
                :param model: - данные о выбранной для изменения модели
                :param key: - внутренний id модели для изменения
                :return: - None
                """
                await show_edit_dialog(
                    e, model,
                    lambda new_data:(
                        update_model_data(cam_name, key, new_data),
                        refresh_data()
                    ),
                    type_flag = 'edit'
                )

            async def on_click_delete(e, key=model_key):
                """
                Функция удаления элемента таблицы и информации о нём из json
                :param e: - событийный параметр  flet
                :param key: - внутренний id модели
                :return:
                """
                async def del_and_refresh():
                    delete_model_data(key, cam_name)
                    refresh_data()
                await show_delete_dialog(
                    e, on_delete_callback = del_and_refresh
                )

            containers.append(
                 Container(
                    content=Column(
                        controls=[
                            Text(f'Информация о нейросети {model_key}',
                                 size=14, color=application_colors['text']),
                            Container(
                                content=Row(
                                    controls=[
                                        Container(
                                            width=25,
                                            height=25,
                                            bgcolor=hex_color(model_data['color']),
                                            border_radius=4,
                                        ),
                                        Container(
                                            content=Column(
                                                controls=[
                                                    Text(model_data["name"], size=18, weight=FontWeight.BOLD,
                                                         color=application_colors['text'],
                                                         ),
                                                    Text(model_data["description"], size=16, weight=FontWeight.NORMAL,
                                                         color=application_colors['text']),
                                                ],
                                                spacing=5
                                            ),
                                            expand=True,

                                        ),
                                        Container(
                                            content=Column(
                                                controls=[
                                                    IconButton(
                                                        ref=container_button_ref,
                                                        icon=icons.EDIT,
                                                        tooltip="Редактировать",
                                                        icon_color=application_colors["inactive"] if not is_edit_mode
                                                                else application_colors["text"],
                                                        on_click=on_click_edit,
                                                        disabled=not is_edit_mode
                                                    ),
                                                    IconButton(
                                                        ref= container_button_ref,
                                                        icon=icons.DELETE,
                                                        tooltip="Удалить",
                                                        icon_color=application_colors["inactive"] if not is_edit_mode
                                                                else application_colors["text"],
                                                        on_click=on_click_delete,
                                                        disabled = not is_edit_mode
                                                    )
                                                ],
                                                horizontal_alignment=CrossAxisAlignment.END,
                                            )

                                        ),

                                    ],
                                    alignment=MainAxisAlignment.START,
                                    vertical_alignment=CrossAxisAlignment.CENTER,
                                    spacing=20
                                ),
                                padding=10,
                                border_radius=20,
                                bgcolor=application_colors['top_bar'],
                                border=border.all(1, colors.GREY),
                            ),
                        ],
                    ),
                    padding=padding.only(right=20)
                ),
            )
        return Column(controls=containers, spacing=10)

    def background_create(cam_name):
        """
        Создание всех элементов страницы
        :param cam_name: - имя камеры
        :return: - вкладку со всеми элементами по выбранной камере
        """
        data = read_settings(cam_name)

        async def on_click_add(e):
            model_data = {"color": [0, 0, 0], "description": '',"name": '', "path": '',"conf":'0.5'}
            await show_edit_dialog(
                e,
                model_data,
                lambda new_data: (
                    new_model_data(cam_name, new_data),
                    refresh_data()
                ),
                type_flag='add'
            )


        info_content = Column(
            controls=[
                Text(f"{cam_name.upper()}", size=20, weight=FontWeight.BOLD, color=application_colors['text']),
                Column(
                    controls=[
                        neural_container(cam_name, data),
                        IconButton(
                            ref=add_button_ref,
                            icon=icons.ADD,
                            tooltip="Добавить",
                            icon_color= application_colors["inactive"] if not is_edit_mode
                                else application_colors["text"],
                            on_click=on_click_add,
                            disabled = not is_edit_mode
                        ),
                    ],
                    horizontal_alignment = CrossAxisAlignment.CENTER,
                )
            ],
            alignment=MainAxisAlignment.CENTER,
            horizontal_alignment=CrossAxisAlignment.START,
            scroll=ScrollMode.AUTO
        )
        container = Container(
            content=info_content,
            width=600,
            height=750,
            padding=20,
            border_radius=20,
            bgcolor=application_colors['background'],
            border=border.all(1, colors.GREY),

        )
        return container


    neural_networks_tab = Tab(
        text='Нейросети',
        content=Column(
            controls=[

                Container(
                    content=Text(
                        value="Нейросети",
                        size=24,
                        weight=FontWeight.BOLD,
                        color=application_colors["text"],
                        text_align=TextAlign.CENTER,
                    ),
                    padding=padding.only(top=20,bottom=5),
                ),
                Container(
                    content=Row(
                        ref=data_column_ref,
                        controls=[
                            background_create(far),
                            background_create(middle),
                            background_create(near),
                         ],
                        alignment=MainAxisAlignment.CENTER,
                     ),
                ),
                Container(
                    content = Row(
                        controls=[
                            ElevatedButton(
                                ref=edit_mode_button_ref,
                                text="Изменить информацию",
                                width=288,
                                height=48,
                                style=default_active_button_style,
                                on_click=change_information
                            ),
                            ElevatedButton(
                                ref=save_button_ref,
                                text="Сохранить",
                                width=288,
                                height=48,
                                style=default_inactive_button_style,
                                on_click= save_information,
                                disabled=True,
                            ),
                            IconButton(
                                ref=change_heights_ref,
                                icon=icons.EDIT,
                                style=default_inactive_button_style,
                                on_click=on_click_heights_edit,
                                disabled=True,
                            ),
                        ],
                        alignment=MainAxisAlignment.CENTER
                    ),
                    padding=padding.only(top=20, bottom=10),
                )
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER
        )
    )
    return neural_networks_tab
