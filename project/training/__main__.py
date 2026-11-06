"""Запуск отдельного мастера сбора датасета.

Windows:
    .venv\\Scripts\\python.exe -m training

Мастер нужно запускать при остановленной производственной программе: обе
программы используют одни и те же USB-камеры и один COM-порт станции, а
``cv2.VideoCapture`` и ``serial.Serial`` нельзя безопасно открыть дважды.

Движение повторяет production-цикл: станция встаёт на координаты ячейки
паллеты по маршруту «змейкой» из ``project/configuration/*.json``. Если
станция не подключена, мастер работает в режиме ``--motion off`` — кадры
снимаются с текущей позиции, а маршрут по ячейкам только помечается.
"""

from __future__ import annotations

import argparse
import json
import os
import webbrowser
from pathlib import Path

import uvicorn

from project.training.cameras import DEFAULT_CAMERA_ROLES, ProjectCameraSource
from project.training.collector import (
    DEFAULT_DEFECT_CLASSES,
    TrainingCollector,
    TrainingConfig,
)
from project.training.pallet import PalletError, PalletOrigin, PalletSettings
from project.training.paths import (
    COORDINATES_FILE,
    LAUNCH_FILE,
    default_dataset_root,
    ensure_project_root,
)
from project.training.server import create_app
from project.training.station import PlanarStation


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Мастер сбора кадров паллеты тремя камерами станции "
            "для обучения YOLO"
        )
    )
    parser.add_argument("--host", default=os.environ.get("TRAINING_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("TRAINING_PORT", "8010")))
    parser.add_argument(
        "--root",
        default=os.environ.get("TRAINING_ROOT", str(default_dataset_root())),
        help="Папка, в которой создаются наборы изображений",
    )
    parser.add_argument("--config", help="JSON с camera_roles и defect_classes")
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument(
        "--motion",
        choices=("auto", "off"),
        default=os.environ.get("TRAINING_MOTION", "auto"),
        help=(
            "auto — станция встаёт на координаты ячеек паллеты через "
            "project.station.requests, off — станция не двигается"
        ),
    )
    parser.add_argument(
        "--serial-port",
        default=os.environ.get("SERIAL_PORT"),
        help="COM-порт станции; по умолчанию ищется автоматически (USB-SERIAL)",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=int(os.environ.get("SERIAL_BAUD", "115200")),
    )
    parser.add_argument(
        "--launch",
        default=str(LAUNCH_FILE),
        help="launch.json с размерами паллеты и шагом между корпусами",
    )
    parser.add_argument(
        "--coordinates",
        default=str(COORDINATES_FILE),
        help="coordinates.json с координатами первой ячейки",
    )
    parser.add_argument(
        "--start-cell",
        type=int,
        default=int(os.environ.get("TRAINING_START_CELL", "1")),
        help="Номер первого корпуса на паллете (по маршруту «змейкой»)",
    )
    parser.add_argument(
        "--indices",
        default=os.environ.get("TRAINING_CAMERA_INDICES"),
        help=(
            "Явное сопоставление камер, например near=0,far=1,middle=2. "
            "По умолчанию порядок камер production-проекта."
        ),
    )
    parser.add_argument(
        "--no-picture-settings",
        action="store_true",
        help=(
            "Не применять яркость/контраст/фильтры из "
            "project/configuration/picture.json"
        ),
    )
    args = parser.parse_args(argv)

    # Production-функции читают JSON по относительным путям
    # project/configuration/..., поэтому рабочая папка — корень репозитория.
    ensure_project_root()

    options = _load_options(args.config)
    roles = tuple(options.get("camera_roles") or DEFAULT_CAMERA_ROLES)
    classes = tuple(options.get("defect_classes") or DEFAULT_DEFECT_CLASSES)
    config = TrainingConfig(
        root_folder=args.root,
        camera_roles=roles,
        defect_classes=classes,
        start_cell=args.start_cell,
        follow_pallet=args.motion != "off",
    )

    # Паллета читается один раз при старте: если конфигурация проекта
    # недоступна, лучше сразу сказать об этом, а не после первого нажатия.
    try:
        pallet = PalletSettings.load(args.launch)
        origin = PalletOrigin.load(args.coordinates)
    except PalletError as exc:
        raise SystemExit(
            f"Не удалось прочитать конфигурацию паллеты: {exc}"
        ) from exc

    cameras = ProjectCameraSource(
        roles=roles,
        indices=_parse_indices(args.indices),
        use_picture_settings=not args.no_picture_settings,
    )
    station = PlanarStation(
        enabled=args.motion != "off",
        port=args.serial_port,
        baudrate=args.baudrate,
        coordinates_file=args.coordinates,
    )
    collector = TrainingCollector(
        config,
        frame_source=cameras,
        station=station if station.enabled else None,
        pallet=pallet,
        origin=origin,
        launch_file=args.launch,
        coordinates_file=args.coordinates,
    )
    app = create_app(collector)
    url = f"http://127.0.0.1:{args.port}/"
    _print_banner(url, pallet, origin, roles, classes, station, args.start_cell)
    if args.open_browser:
        webbrowser.open(url)
    try:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    finally:
        cameras.release()
        station.close()


def _print_banner(url, pallet, origin, roles, classes, station, start_cell) -> None:
    print("=" * 72)
    print("Мастер сбора датасета YOLO для планарной станции")
    print(f"Откройте {url}")
    print("Линия должна быть остановлена; камеры и COM-порт заняты только мастером.")
    print(
        f"Паллета: {pallet.rows}×{pallet.columns} = {pallet.total} корпусов, "
        f"шаг {pallet.step_x}×{pallet.step_y} мм, старт с ячейки {start_cell}."
    )
    print(
        "Первая ячейка: "
        f"X={origin.x} Y={origin.y} Z={origin.z} "
        "(project/configuration/coordinates.json)"
    )
    print("Камеры по порядку: " + ", ".join(roles))
    print("Классы дефектов: " + ", ".join(classes))
    if station.enabled:
        print(
            "Движение: станция встаёт на координаты ячейки (G0 через "
            "project.station.requests.move_to_coordinates)."
        )
    else:
        print(
            "Движение отключено (--motion off): кадры снимаются с текущей "
            "позиции станции."
        )
    print("=" * 72)


def _load_options(path: str | None) -> dict:
    if not path:
        return {}
    try:
        with Path(path).open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Не удалось прочитать {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("Конфигурация мастера должна быть JSON-объектом")
    return value


def _parse_indices(value: str | None) -> dict[str, int] | None:
    if not value:
        return None
    result: dict[str, int] = {}
    for chunk in value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "=" not in chunk:
            raise SystemExit(
                "Формат --indices: near=0,far=1,middle=2"
            )
        role, index = chunk.split("=", 1)
        role = role.strip()
        try:
            result[role] = int(index.strip())
        except ValueError as exc:
            raise SystemExit(f"Индекс камеры должен быть числом: {chunk}") from exc
    return result or None


if __name__ == "__main__":
    main()
