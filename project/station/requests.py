"""
Файл описывает основные функции управления роботом через G-коды.
"""
import time
import math
import serial

from project.configuration.worker import write_to_json, read_from_json


def send_command(serial_connection, command):
    """
    Отправляет команду через установленное подключение и возвращает ответ.

    param serial_connection: Объект подключения (serial.Serial).
    param command: Команда для отправки (str).
    return: Ответ от устройства (str) или None в случае ошибки.
    """
    try:
        if not serial_connection.is_open:
            raise ConnectionError("Ошибка: Соединение с устройством отсутствует.")

        serial_connection.write(f'{command}\n'.encode('utf-8'))
        response = serial_connection.readline().decode('utf-8').strip()
        return response if response else None

    except serial.SerialException as e:
        print(f"Ошибка при отправке команды: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None


def move_to_coordinates(serial_connection, x=None, y=None, z=None):
    """
    Перемещает устройство к заданным координатам.

    param serial_connection: Объект подключения (serial.Serial).
    param x: Координата X (float) или None, если не изменяется.
    param y: Координата Y (float) или None, если не изменяется.
    param z: Координата Z (float) или None, если не изменяется.
    """
    max_speed_z = 5
    max_speed_xy = 25

    if not serial_connection.is_open:
        raise ConnectionError("Ошибка: Соединение с устройством отсутствует.")
    prev_x = read_from_json(
        "project/configuration/coordinates.json",
        "current_coordinate_of_the_station_by_x")
    prev_y = read_from_json(
        "project/configuration/coordinates.json",
        "current_coordinate_of_the_station_by_y")
    prev_z = read_from_json(
        "project/configuration/coordinates.json",
        "current_coordinate_of_the_station_by_z")

    target_x = x if x is not None else prev_x
    target_y = y if y is not None else prev_y
    target_z = z if z is not None else prev_z

    def calculate_travel_time(x1, y1, z1, x2, y2, z2):
        """ Рассчитывает время передвижения по XY и Z, выбирает максимальное. """
        distance_xy = math.hypot(x2 - x1, y2 - y1)
        distance_z = abs(z2 - z1)
        return max(distance_xy / max_speed_xy, distance_z / max_speed_z)

    travel_time = calculate_travel_time(prev_x, prev_y, prev_z, target_x, target_y, target_z)

    command = (f'G0{" X" + str(target_x) if x is not None else ""}'
               f'{" Y" + str(target_y) if y is not None else ""}'
               f'{" Z" + str(target_z) if z is not None else ""}')

    send_command(serial_connection, command)

    start_time = time.time()
    while time.time() - start_time < travel_time:
        if not serial_connection.is_open:
            raise ConnectionError(
                "Ошибка: Соединение с устройством разорвано во время перемещения.")
        time.sleep(1)

    write_to_json(
        "project/configuration/coordinates.json",
        "current_coordinate_of_the_station_by_x",
        round(target_x, 3))
    write_to_json(
        "project/configuration/coordinates.json",
        "current_coordinate_of_the_station_by_y",
        round(target_y, 3))
    write_to_json(
        "project/configuration/coordinates.json",
        "current_coordinate_of_the_station_by_z",
        round(target_z, 3))


def move_to_home(serial_connection):
    """
    Перемещает устройство в домашнюю позицию (нулевые координаты).

    param serial_connection: Объект подключения (serial.Serial).
    """
    try:
        if not serial_connection.is_open:
            raise ConnectionError("Ошибка: Соединение с устройством отсутствует.")

        send_command(serial_connection, 'G28')

        while True:
            response = send_command(serial_connection, 'M27')

            if response and "busy: processing" not in response:
                write_to_json(
                    "project/configuration/coordinates.json",
                    "current_coordinate_of_the_station_by_x",
                    0)
                write_to_json(
                    "project/configuration/coordinates.json",
                    "current_coordinate_of_the_station_by_y",
                    0)
                write_to_json(
                    "project/configuration/coordinates.json",
                    "current_coordinate_of_the_station_by_z",
                    0)
                break
        move_to_coordinates(serial_connection,0,0,7) # было 7 в Z
    except Exception as e:
        print(f"Ошибка при перемещении в нулевые координаты: {e}")
        raise
