"""
Скрипт, запускающий управляющее Flet-приложение.
"""
import flet as ft

from project.application.build import building_the_application

ft.app(target=building_the_application)
