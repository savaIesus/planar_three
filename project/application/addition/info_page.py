from flet import *

from project.station.weights.networks_vault import middle, near, far  # общие названия камер
from project.configuration.worker import hex_color
from project.application.addition.colors import color_mode
import project.station.weights.networks_vault as nv

application_colors = color_mode()
elements_ref = Ref()

def block_list(lst, n):
    """Разбивает список lst на блоки по n элементов"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def info_page():
    """
    Создаёт обновляемую панель с названием и цветом нейросетей
    Returns:
    колонку с элементами
    """
    global elements_ref
    return Column(ref=elements_ref, controls=info_create(), spacing=10, width=550)

def info_create():
    elements = []
    temp_list = []
    for cam_key in [middle, far, near]:
        model_list = nv.models.get(cam_key, [])
        for _, color, name,_ in model_list:
            storage = (color, name)
            if storage not in temp_list:
                temp_list.append(storage)
                elements.append(
                    Container(
                        content=Row(
                            controls=[
                                Container(
                                    width=18,
                                    height=18,
                                    bgcolor=hex_color(color),
                                    border_radius=2,
                                ),
                                Text(name,
                                     size=16,
                                     weight=FontWeight.BOLD,
                                     color=application_colors['text']
                                     )
                            ]
                        )
                    ),
                )
    rows = []
    temp_list.clear()
    for chunk in block_list(elements, 3):
        rows.append(
            Row(
                controls=chunk,
                spacing=10,
                alignment=MainAxisAlignment.CENTER,
                vertical_alignment=CrossAxisAlignment.CENTER
            )
        )
    return rows


def info_page_update():
    """
    Функция обновления панели в случае нажатия клавиши 'Сохранить' в списке нейросетей
    Returns:
    None
    """
    global elements_ref

    if elements_ref.current is None:
        return

    elements_ref.current.controls.clear()
    elements_ref.current.controls.extend(
        info_create()
    )
    elements_ref.current.update()