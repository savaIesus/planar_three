import os
import json
import threading
import shutil
lock = threading.Lock()

def hex_color(rgb):
    return '#%02x%02x%02x' % tuple(rgb) # реобразование цвета в HEX

def shorten_path(full_path, folders_to_show=4):

    # Приводим к нормальному пути
    full_path = os.path.normpath(full_path)
    parts = full_path.split(os.sep)  # разбиваем по разделителю папок

    # Если путь заканчивается на файл, отделим имя файла
    if os.path.isfile(full_path):
        filename = parts[-1]
        folders = parts[:-1]
    else:
        filename = ""
        folders = parts

    # Берём последние N папок
    last_folders = folders[-folders_to_show:]

    # Склеиваем обратно
    short_path = os.sep.join(last_folders)
    if filename:
        short_path = os.path.join(short_path, filename)

    return short_path

def copy_file(source_path, destination_path):
    if os.path.isfile(source_path) and os.path.isdir(destination_path):
        try:
            shutil.copy(source_path, destination_path)
            print(f"Файл успешно скопирован в {shorten_path(destination_path)}")
        except FileNotFoundError:
            print("Ошибка: Один из путей не найден.")
        except Exception as ex:
            print(f'Произошла ошибка при копировании:{ex}')

def append_distances_to_json(file_path, distances):
    """
    Записывает данные в JSON файл. Если файл не существует, создает его.
    Параметры:
        filename (str): Имя файла, в который будут записаны данные
        distances (list): Список размеров расстояний между выводами.
    """
    try:
        # Читаем существующие данные
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)  # Загружаем существующий JSON
    except (FileNotFoundError, json.JSONDecodeError):
        data = []  # Если файла нет или он пуст, создаем новый список

    # Добавляем новый список в данные
    data.append(distances)

    # Записываем обратно в файл
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# def check_file_or_create(path:str):
#     try:
#         dir_path = os.path.dirname(path)
#         if dir_path:
#             os.makedirs(path, exist_ok = True)
#
#         if not os.path.exists(path):
#             with open(path, 'w', encoding="UTF-8") as file:
#                 json.dump( {}, file, indent=0)
#     except Exception as ex:
#         print(f'Ошибка создания/проверки файла: {ex}')

def write_to_json(path, key, value):
    """
    Записывает данные в JSON файл. Если файл не существует, создает его.
    Параметры:
        filename (str): Имя файла, в который будут записаны данные.
        key (str): Ключ, по которому будет сохранено значение.
        value (any): Значение, которое будет записано по указанному ключу.
    """
    with lock:
        # Проверяем, существует ли файл
        if os.path.exists(path):
            # Если файл существует, читаем его содержимое
            with open(path, 'r', encoding="UTF-8") as file:
                data = json.load(file)
        else:
            # Если файл не существует, создаем пустой словарь
            data = {}

        # Обновляем или добавляем значение по ключу
        data[key] = value

        # Записываем обновленные данные обратно в файл
        with open(path, 'w', encoding="UTF-8") as file:
            json.dump(data, file, indent=4)


def read_from_json(path, key):
    """
    Читает данные из JSON файла по указанному ключу.
    Параметры:
        filename (str): Имя файла, из которого будут прочитаны данные.(путь через /)
        key (str): Ключ, по которому будет извлечено значение.
    Возвращает:
        any: Значение по указанному ключу, если ключ существует. Иначе None.
    """
    with lock:
        # Проверяем, существует ли файл
        if os.path.exists(path):
            # Если файл существует, читаем его содержимое
            with open(path, 'r', encoding="UTF-8") as file:
                data = json.load(file)

            # Возвращаем значение по ключу, если ключ существует
            return data.get(key, None)

        return None

def read_json_to_list(path):
    try:
        with open(path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            # Проверяем, что данные являются списком списков (двумерным списком)
            if isinstance(data, list) and all(isinstance(sublist, list) for sublist in data):
                return data

            raise ValueError("Данные в JSON-файле не являются двумерным списком")

    except FileNotFoundError:
        print(f"Ошибка: Файл {path} не найден")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: Файл {path} содержит некорректный JSON")
        return None
    except ValueError as e:
        print(e)
        return None
