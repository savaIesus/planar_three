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
    global elements_ref
    return Column(ref=elements_ref, controls=info_create(), spacing=10)

def info_create():
    elements = []
    for cam_key in [middle, far, near]:
        model_list = nv.models.get(cam_key, [])
        for _, color, name in model_list:
            elements.append(
                Container(
                    content=Row(
                        controls=[
                            Container(
                                width=25,
                                height=25,
                                bgcolor=hex_color(color),
                                border_radius=4,
                            ),
                            Text(name,
                                 size=18,
                                 weight=FontWeight.BOLD,
                                 color=application_colors['text']
                                 )
                        ]
                    )
                ),
            )
    rows = []
    for chunk in block_list(elements, 5):
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
    global elements_ref

    if elements_ref.current is None:
        return

    elements_ref.current.controls.clear()
    elements_ref.current.controls.extend(
        info_create()
    )
    elements_ref.current.update()