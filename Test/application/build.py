from flet import *


from Test.application.addition.colors import color_mode
from Test.application.layers_list import create_layers_list

def build_the_application(application_page: Page):
    """
    Настраивает основное окно приложения, добавляет необходимые вкладки.
    Параметры: основное окно приложения application_page - flet.Page.
    """
    application_page.window_width = 1920
    application_page.window_height = 1080
    application_page.window_maximized = True

    application_page.title = 'Тестовая программа для проверки функций'
    application_page.vertical_alignment = MainAxisAlignment.CENTER
    application_page.horizontal_alignment = CrossAxisAlignment.CENTER

    #Цветовая гамма приложения
    application_colors = color_mode()
    application_page.bgcolor = application_colors['background']
    application_page.theme = Theme(
        slider_theme = SliderTheme(disabled_thumb_color=application_colors['active'])
    )

    application_tabs = Tabs(
        tabs =  create_layers_list(),
        expand = True,
        selected_index=0,
        animation_duration = 400,
        label_color = application_colors["active"],
        unselected_label_color = application_colors["text"],
        indicator_tab_size=True
    )
    application_page.add(application_tabs)