from project.configuration.worker import read_from_json


def get_path():
    """
    Загружает изображение load.gif либо в тёмном, либо в
    светлом варианте в зависимости от выбранной темы.
    :return: None
    """
    if read_from_json("project/configuration/launch.json", "theme") == "light":
        return "project/application/video/load_light.gif"

    return "project/application/video/load.gif"
