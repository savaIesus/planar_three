from project.application.layers.camera_mechanical import create_camera_mechanical_layer
from project.application.layers.distribution import create_layout_control_tab
from project.application.layers.guide import create_guide_layer
from project.application.layers.measurement import create_measurements_tab
from project.application.layers.picture import create_picture_layer
from project.application.layers.stats import create_stats_layer
from project.application.layers.workspace import create_workspace_layer
from project.application.layers.statistics import create_statistics_layer
from project.application.layers.calibration import create_calibration_layer
from project.application.layers.quality_map import create_quality_map_layer
from project.application.layers.networks_list import create_neural_networks_list
def create_layers_list():
    """
    Создаёт и возвращает список слоёв (вкладок) приложения.
    Возвращает список объектов слоёв приложения.
    """
    tabs_list = [
        create_workspace_layer(),
        # create_quality_map_layer(),
        create_calibration_layer(),
        create_camera_mechanical_layer(),
        create_neural_networks_list(),
        create_measurements_tab(),
        create_picture_layer(),
        # create_statistics_layer(),
        create_stats_layer(),
        create_layout_control_tab(),
        create_guide_layer()
    ]

    return tabs_list
