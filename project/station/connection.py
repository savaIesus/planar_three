"""
Файл описывает установление и контроль подключения к роботу через COM-порт.
"""
import serial
import serial.tools.list_ports

from project.application.addition.error_message import show_error


def detect_port():
    """
    Находит первый порт с описанием, содержащим 'USB-SERIAL'.
    Возвращает строку с именем порта или None, если порт не найден.
    """
    try:
        ports = serial.tools.list_ports.comports()
        # Поиск порта, который содержит 'USB-SERIAL' в описании (регистронезависимо)
        for port in ports:
            if "USB-SERIAL" in port.description.upper():
                return port.device
        # Если ничего не найдено
        print("Порт с 'USB-SERIAL' не найден.")
        return None
    except Exception as e:
        print(f"Ошибка при поиске порта: {e}")
        return None


def define_presets(port=None, baudrate=115200, timeout=1):
    """
    Определяет настройки подключения: порт, скорость передачи данных, таймаут.
    Если порт не задан явно, он ищется автоматически.

    :param port: имя COM-порта или None для автопоиска
    :param baudrate: скорость обмена
    :param timeout: таймаут чтения, с
    :return: список [порт, скорость, таймаут]
    """
    if port is None:
        port = detect_port()
    if port is None:
        raise ValueError("Не удалось найти подходящий COM-порт.")

    return [port, baudrate, timeout]


def establish_connection(app_page=None, port=None, baudrate=115200, timeout=1):
    """
    Устанавливает подключение через Serial.
    Возвращает объект подключения или None, если подключение не удалось.

    :param app_page: страница Flet для показа диалога ошибки; может быть None,
                     если вызывающий код не связан с интерфейсом
                     (например, мастер сбора датасета)
    :param port: имя COM-порта; None — автопоиск по описанию 'USB-SERIAL'
    :param baudrate: скорость обмена
    :param timeout: таймаут чтения, с
    """
    try:
        port, baudrate, timeout = define_presets(port, baudrate, timeout)
        connection = serial.Serial(port, baudrate, timeout=timeout)

        # Очищаем входной и выходной буферы
        connection.reset_input_buffer()
        connection.reset_output_buffer()

        if connection.is_open:
            print(f"Подключение установлено: {port} @ {baudrate} bps")
            return connection

        print("Не удалось открыть соединение.")
        return None

    except serial.SerialException as e:
        print(f"Ошибка при подключении: {e}")
        return None

    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
        if app_page is not None:
            show_error("Ошибка конфигурации!", e, app_page)
        return None


def close_connection(connection):
    """
    Закрывает подключение, если оно открыто.
    """
    try:
        if connection and connection.is_open:
            connection.close()
            print("Соединение успешно закрыто.")
        else:
            print("Соединение уже закрыто или не было установлено.")

    except Exception as e:
        print(f"Ошибка при закрытии соединения: {e}")
