def set_object_state(input_object, state):
    """
    Устанавливает состояние объекта (включение или отключение) и обновляет их состояние.

    Параметры:
    button (Button): Кнопка, состояние которой нужно изменить.
    state (bool): True для отключения, False для включения. По умолчанию True.

    Возвращает:
    None
    """
    try:
        input_object.disabled = state
        input_object.update()
    except Exception as e:
        message = "отключении" if state else "включении"
        print(f"Ошибка при {message} кнопок: {e}")
