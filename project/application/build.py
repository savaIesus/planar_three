import threading

from flet import *

from project.application.list import create_layers_list
from project.application.addition.colors import color_mode
import project.station.weights.networks_vault as nv

def building_the_application(application_page: Page):
    """
    Настраивает основное окно приложения, добавляет необходимые вкладки.
    Параметры: основное окно приложения application_page - flet.Page.
    """
    threading.Thread(target=nv.networks_init(), daemon=True).start()
    # Настройка окна приложения
    application_page.window_width = 1920
    application_page.window_height = 1080
    application_page.window_maximized = True

    application_page.title = "Управление системой"
    application_page.vertical_alignment = MainAxisAlignment.CENTER
    application_page.horizontal_alignment = CrossAxisAlignment.CENTER

    # Настройка цветовой гаммы приложения
    application_colors = color_mode()
    application_page.bgcolor = application_colors["background"]
    application_page.theme = Theme(
        slider_theme=SliderTheme(disabled_thumb_color=application_colors["active"]),
    )

    # Создание и добавление вкладок в окно приложения
    application_tabs = Tabs(
        tabs=create_layers_list(),
        expand=True,
        selected_index=0,
        animation_duration=400,
        label_color=application_colors["active"],
        divider_color=application_colors["top_bar"],
        indicator_color=application_colors["active"],
        unselected_label_color=application_colors["text"],
        indicator_tab_size=True,
    )

    application_page.add(application_tabs)


