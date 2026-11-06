"""Пути production-проекта, с которыми работает мастер сбора датасета.

Мастер обязан читать ровно те же настройки, что и основное приложение:
координаты первой ячейки, размеры паллеты и параметры картинки. Все пути
собраны в одном модуле, чтобы при переносе каталогов правилось одно место.
"""

from __future__ import annotations

import os
from pathlib import Path

# project/training/paths.py → project/training → project → корень репозитория
REPO_ROOT = Path(__file__).resolve().parents[2]

CONFIGURATION_DIR = REPO_ROOT / "project" / "configuration"
STATION_DIR = REPO_ROOT / "project" / "station"

LAUNCH_FILE = CONFIGURATION_DIR / "launch.json"
COORDINATES_FILE = CONFIGURATION_DIR / "coordinates.json"
PICTURE_FILE = CONFIGURATION_DIR / "picture.json"
STATUSES_FILE = STATION_DIR / "statuses.json"

DEFAULT_DATASET_ROOT = CONFIGURATION_DIR.parent.parent / "training_datasets"


def production_path(path: str | os.PathLike[str]) -> str:
    """Путь в виде, который принимают функции production-проекта.

    ``move_to_coordinates``, ``read_from_json`` и ``apply_settings_to_frame``
    обращаются к файлам по относительным POSIX-путям
    (``project/configuration/coordinates.json``). Поэтому абсолютный путь
    переводится в относительный от корня репозитория.
    """
    absolute = Path(path).expanduser()
    if not absolute.is_absolute():
        return Path(absolute).as_posix()
    try:
        return absolute.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        # Файл вне репозитория: production-функция всё равно его прочитает,
        # но только если ей передать абсолютный путь.
        return absolute.resolve().as_posix()


def resolve_config_path(path: str | os.PathLike[str]) -> Path:
    """Найти файл конфигурации проекта независимо от текущего каталога.

    ``move_to_coordinates``/``read_from_json`` из production-проекта читают
    ``project/configuration/*.json`` относительно рабочего каталога. Мастер
    читает те же файлы сам (паллета, координаты), поэтому путь проверяется
    и относительно ``cwd``, и относительно корня репозитория.
    """
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    if candidate.exists():
        return candidate.resolve()
    return (REPO_ROOT / candidate).resolve()


def ensure_project_root() -> Path:
    """Перейти в корень репозитория, если мастер запущен из другого каталога.

    Production-функции работают с JSON по относительным путям
    ``project/configuration/...``, поэтому рабочий каталог должен быть
    корнем репозитория (как при запуске ``main.py``).
    """
    if Path.cwd().resolve() != REPO_ROOT:
        os.chdir(REPO_ROOT)
    return REPO_ROOT


def default_dataset_root() -> Path:
    """Папка датасетов по умолчанию — рядом с production-конфигурацией."""
    return DEFAULT_DATASET_ROOT
