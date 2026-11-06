"""Паллета корпусов: маршрут «змейкой» и координаты ячеек.

Модуль повторяет ту же геометрию, по которой ездит производственный
алгоритм :func:`project.alghorithms.core.main_algorithm`:

* старт — ячейка 0, её координаты лежат в ``coordinates.json``
  (``*_coordinate_of_the_first_cell``);
* при чётном ряду робот едет вдоль паллеты в сторону увеличения X, при
  нечётном — в сторону уменьшения (возвращается «змейкой»);
* переход на следующий ряд — смещение по Y на
  ``distance_between_vertical_centers``;
* шаг внутри ряда — ``distance_between_horizontal_centers``.

Номера ячеек 1..N идут в том же порядке, в котором их обходит
``main_algorithm`` (слева направо в чётных рядах, справа налево в нечётных),
поэтому учебные кадры привязываются к реальным номерам корпусов на паллете.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from project.training.paths import COORDINATES_FILE, LAUNCH_FILE, resolve_config_path


class PalletError(RuntimeError):
    """Не удалось прочитать размеры паллеты или координаты ячеек."""


_FILE_LOCK = threading.RLock()


def _read_json(path: Path) -> dict[str, Any]:
    resolved = resolve_config_path(path)
    try:
        with resolved.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise PalletError(
            f"Не удалось прочитать {resolved.name}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise PalletError(f"{resolved.name} должен содержать JSON-объект")
    return value


def _number(data: dict[str, Any], key: str) -> float:
    value = data.get(key)
    if value is None:
        raise PalletError(f"В конфигурации нет параметра {key}")
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise PalletError(f"Параметр {key} должен быть числом") from exc


@dataclass(frozen=True)
class PalletSettings:
    """Размеры паллеты и шаг между центрами корпусов (как в launch.json)."""

    rows: int
    columns: int
    step_x: float
    step_y: float

    @classmethod
    def load(cls, launch_file: str | Path = LAUNCH_FILE) -> "PalletSettings":
        data = _read_json(Path(launch_file))
        rows = _positive_int(data, "number_of_rows")
        columns = _positive_int(data, "number_of_columns")
        return cls(
            rows=rows,
            columns=columns,
            step_x=_number(data, "distance_between_horizontal_centers"),
            step_y=_number(data, "distance_between_vertical_centers"),
        )

    @property
    def total(self) -> int:
        return self.rows * self.columns

    def to_dict(self) -> dict[str, Any]:
        return {
            "rows": self.rows,
            "columns": self.columns,
            "step_x": self.step_x,
            "step_y": self.step_y,
            "total": self.total,
        }


def _positive_int(data: dict[str, Any], key: str) -> int:
    value = _number(data, key)
    if value < 1:
        raise PalletError(f"Параметр {key} должен быть не меньше 1")
    return int(round(value))


@dataclass(frozen=True)
class PalletOrigin:
    """Координаты центра первого корпуса паллеты."""

    x: float
    y: float
    z: float

    @classmethod
    def load(
        cls,
        coordinates_file: str | Path = COORDINATES_FILE,
    ) -> "PalletOrigin":
        data = _read_json(Path(coordinates_file))
        return cls(
            x=_number(data, "x_coordinate_of_the_first_cell"),
            y=_number(data, "y_coordinate_of_the_first_cell"),
            z=_number(data, "z_coordinate_of_the_first_cell"),
        )


@dataclass(frozen=True)
class Cell:
    """Одна ячейка паллеты (один корпус под тремя камерами)."""

    cell_id: int          # номер по маршруту «змейкой», начиная с 1
    row: int              # ряд с нуля
    column: int           # колонка с нуля
    x: float
    y: float
    z: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cell_id": self.cell_id,
            "row": self.row,
            "column": self.column,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z": round(self.z, 3),
        }


def cell_coordinates(
    settings: PalletSettings,
    origin: PalletOrigin,
    row: int,
    column: int,
) -> tuple[float, float, float]:
    """Координаты ячейки ``row, column`` по геометрии production-алгоритма."""
    if not 0 <= row < settings.rows:
        raise PalletError(f"Ряд {row} вне паллеты ({settings.rows} рядов)")
    if not 0 <= column < settings.columns:
        raise PalletError(
            f"Колонка {column} вне паллеты ({settings.columns} колонок)"
        )
    if row % 2 == 0:
        # Чётный ряд: движение по возрастанию X.
        x = origin.x + column * settings.step_x
    else:
        # Нечётный ряд: робот возвращается и идёт по убыванию X.
        x = origin.x + (settings.columns - 1 - column) * settings.step_x
    y = origin.y - row * settings.step_y
    return x, y, origin.z


def build_route(settings: PalletSettings, origin: PalletOrigin) -> list[Cell]:
    """Полный маршрут по паллете в порядке обхода production-алгоритма."""
    route: list[Cell] = []
    cell_id = 1
    for row in range(settings.rows):
        for column in range(settings.columns):
            x, y, z = cell_coordinates(settings, origin, row, column)
            route.append(
                Cell(
                    cell_id=cell_id,
                    row=row,
                    column=column,
                    x=x,
                    y=y,
                    z=z,
                )
            )
            cell_id += 1
    return route


def iterate_route(
    settings: PalletSettings,
    origin: PalletOrigin,
) -> Iterator[Cell]:
    yield from build_route(settings, origin)


def cell_number(row: int, column: int, columns: int) -> int:
    """Номер ячейки (с единицы) для ряда и колонки."""
    return row * columns + column + 1


def row_column(cell_id: int, columns: int) -> tuple[int, int]:
    """Обратное преобразование номера ячейки в ``(row, column)``."""
    if cell_id < 1:
        raise PalletError("Номер ячейки начинается с 1")
    return (cell_id - 1) // columns, (cell_id - 1) % columns


COORDINATE_KEYS = (
    "current_coordinate_of_the_station_by_x",
    "current_coordinate_of_the_station_by_y",
    "current_coordinate_of_the_station_by_z",
)


def read_current_coordinates(
    coordinates_file: str | Path = COORDINATES_FILE,
) -> tuple[float, float, float]:
    """Текущая (расчётная) позиция станции из ``coordinates.json``."""
    data = _read_json(Path(coordinates_file))
    return tuple(_number(data, key) for key in COORDINATE_KEYS)  # type: ignore[return-value]


def write_current_coordinates(
    x: float,
    y: float,
    z: float,
    coordinates_file: str | Path = COORDINATES_FILE,
) -> None:
    """Записать расчётную позицию станции.

    ``move_to_coordinates`` из production-проекта уже делает это сам, поэтому
    функция нужна только когда движение выполнялось напрямую через
    :class:`StationConnection` (ровно так же поступает ``move_to_home``).
    """
    path = resolve_config_path(coordinates_file)
    with _FILE_LOCK:
        data = _read_json(path)
        data[COORDINATE_KEYS[0]] = round(float(x), 3)
        data[COORDINATE_KEYS[1]] = round(float(y), 3)
        data[COORDINATE_KEYS[2]] = round(float(z), 3)
        temporary = path.with_name(f".{path.name}.tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=4)
        temporary.replace(path)


def home_position(launch_file: str | Path = LAUNCH_FILE) -> float:
    """Высота парковки после ``G28`` — как в ``move_to_home``.

    ``move_to_home`` вызывает ``move_to_coordinates(connection, 0, 0, 7)``,
    поэтому после парковки станция стоит в Z = 7. Если в конфигурации
    появится отдельный ключ, он будет использован первым.
    """
    data = _read_json(Path(launch_file))
    for key in (
        "parking_z_after_home",
        "home_z_coordinate",
        "z_coordinate_after_homing",
    ):
        if data.get(key) is not None:
            return _number(data, key)
    return 7.0
