"""Проверка мастера сбора датасета без оборудования.

Станция подменяется записывающей заглушкой, камеры — генератором кадров,
а HTTP-слой проверяется через ``httpx.ASGITransport``.

Запуск:
    python -m pytest project/training/tests -q
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from project.training.collector import (
    CollectorError,
    TrainingCollector,
    TrainingConfig,
)
from project.training.pallet import (
    PalletOrigin,
    PalletSettings,
    build_route,
    cell_coordinates,
)
from project.training.paths import COORDINATES_FILE, LAUNCH_FILE
from project.training.station import MoveResult


class FakeCameras:
    """Источник кадров: монотонные картинки по ролям."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.offset = 0

    def capture_single(self, role: str):
        self.calls.append(role)
        self.offset += 1
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :] = (self.offset * 3 % 255, 40, 90)
        return frame


class FakeStation:
    """Станция-заглушка: запоминает ячейки, на которые её отправили."""

    def __init__(self) -> None:
        self.moves: list[int] = []
        self.homed = 0
        self.fail_on: int | None = None
        self.position = (7.6, 218.3, 2.2)

    def move_to_cell(self, cell):
        if self.fail_on is not None and cell.cell_id == self.fail_on:
            raise RuntimeError("нет связи с контроллером")
        self.moves.append(cell.cell_id)
        self.position = (cell.x, cell.y, cell.z)
        return MoveResult(
            moved=True,
            x=cell.x,
            y=cell.y,
            z=cell.z,
            previous=self.position,
            settle_seconds=0.5,
        )

    def home(self):
        self.homed += 1
        self.position = (0.0, 0.0, 7.0)
        return MoveResult(
            moved=True,
            x=0.0,
            y=0.0,
            z=7.0,
            previous=(0.0, 0.0, 0.0),
            settle_seconds=0.5,
        )

    def status(self):
        x, y, z = self.position
        return {
            "enabled": True,
            "connected": True,
            "position": {"x": x, "y": y, "z": z},
        }


@pytest.fixture()
def pallet() -> tuple[PalletSettings, PalletOrigin]:
    return PalletSettings.load(LAUNCH_FILE), PalletOrigin.load(COORDINATES_FILE)


@pytest.fixture()
def collector(tmp_path: Path, pallet) -> TrainingCollector:
    settings, origin = pallet
    return TrainingCollector(
        TrainingConfig(root_folder=tmp_path / "datasets", start_cell=1),
        frame_source=FakeCameras(),
        station=FakeStation(),
        pallet=settings,
        origin=origin,
    )


def test_route_matches_production_snake(pallet):
    settings, origin = pallet
    route = build_route(settings, origin)
    assert len(route) == settings.total
    # Чётный ряд: X растёт, нечётный — убывает; Y всегда уменьшается.
    assert [cell.column for cell in route[: settings.columns]] == list(
        range(settings.columns)
    )
    second_row = route[settings.columns : 2 * settings.columns]
    # Нечётный ряд идёт обратно, к началу паллеты.
    assert second_row[0].x > second_row[-1].x
    assert second_row[0].y < route[0].y
    x0, y0, z0 = cell_coordinates(settings, origin, 0, 0)
    assert (x0, y0, z0) == (origin.x, origin.y, origin.z)
    x1, y1, _ = cell_coordinates(settings, origin, 1, 0)
    assert x1 == pytest.approx(origin.x + (settings.columns - 1) * settings.step_x)
    assert y1 == pytest.approx(origin.y - settings.step_y)


def test_full_cell_cycle_uses_station(collector: TrainingCollector, tmp_path: Path):
    cameras: FakeCameras = collector.frame_source
    station: FakeStation = collector.station

    state = collector.start_session("тест")
    assert state["session"]["camera_roles"] == ["near", "far", "middle"]
    assert state["next_cell"]["cell_id"] == 1
    assert state["pallet"]["total"] > 0

    state = collector.begin_part()
    part = state["part"]
    assert part["cell_id"] == 1
    assert part["coordinates"]["x"] == pytest.approx(7.6)
    assert station.moves == [1]

    for role in ("near", "far", "middle"):
        record = collector.capture_next()
        assert record.camera_role == role
        assert record.cell_id == 1
        collector.skip_current()
    assert cameras.calls == ["near", "far", "middle"]

    finished = collector.finish_part()
    assert finished["finished_part"]["cell_id"] == 1
    # Между корпусами станция не двигается: движение делает begin_part.
    assert station.moves == [1]

    state = collector.begin_part()
    assert state["part"]["cell_id"] == 2
    assert station.moves == [1, 2]
    assert state["cells"][0]["collected"] is True


def test_part_requires_all_cameras(collector: TrainingCollector):
    collector.start_session("тест")
    collector.begin_part()
    collector.capture_next()
    collector.skip_current()
    with pytest.raises(CollectorError):
        collector.finish_part()


def test_station_failure_keeps_session_clean(collector: TrainingCollector):
    station: FakeStation = collector.station
    station.fail_on = 2
    collector.start_session("тест")
    collector.begin_part()
    for _ in range(3):
        collector.capture_next()
        collector.skip_current()
    collector.finish_part()
    with pytest.raises(CollectorError):
        collector.begin_part()
    state = collector.snapshot()
    assert state["part"] is None
    assert state["next_cell"]["cell_id"] == 2
    station.fail_on = None
    assert collector.begin_part()["part"]["cell_id"] == 2


def test_annotations_and_yolo_export(collector: TrainingCollector, tmp_path: Path):
    collector.start_session("тест")
    collector.begin_part()
    collector.capture_next()
    record = collector.annotate_current(
        defect_class="flatness",
        annotations=[
            {
                "class_name": "flatness",
                "points": [
                    {"x": 10, "y": 10},
                    {"x": 120, "y": 12},
                    {"x": 118, "y": 90},
                ],
            }
        ],
    )
    assert record.has_defect
    label = (collector.store.session_folder / record.label).read_text(encoding="utf-8")
    assert label.split()[0] == str(
        list(collector.config.defect_classes).index("flatness")
    )
    for _ in range(2):
        collector.capture_next()
        collector.skip_current()
    collector.finish_part()
    result = collector.finish_session()
    yolo = result["yolo"]
    assert yolo["task"] == "segment"
    assert yolo["train_count"] + yolo["validation_count"] == 3
    yaml_text = Path(yolo["yaml_path"]).read_text(encoding="utf-8")
    assert "names:" in yaml_text
    session = json.loads(
        (collector.store.session_folder / "session.json").read_text(encoding="utf-8")
    )
    assert session["parts"][0]["cell_id"] == 1


def test_pallet_limits_start_cell(tmp_path: Path, pallet):
    settings, origin = pallet
    collector = TrainingCollector(
        TrainingConfig(root_folder=tmp_path / "datasets"),
        frame_source=FakeCameras(),
        station=FakeStation(),
        pallet=settings,
        origin=origin,
    )
    with pytest.raises(Exception):
        collector.start_session("тест", start_cell=settings.total + 1)


def test_http_flow(tmp_path: Path, pallet):
    from fastapi.testclient import TestClient

    from project.training.server import create_app

    settings, origin = pallet
    collector = TrainingCollector(
        TrainingConfig(root_folder=tmp_path / "datasets"),
        frame_source=FakeCameras(),
        station=FakeStation(),
        pallet=settings,
        origin=origin,
    )
    client = TestClient(create_app(collector))

    config = client.get("/api/training/config").json()
    assert config["camera_roles"] == ["near", "far", "middle"]
    assert config["pallet"]["rows"] == settings.rows

    session = client.post(
        "/api/training/session",
        json={"dataset_name": "http", "start_cell": 1},
    )
    assert session.status_code == 200, session.text

    part = client.post("/api/training/parts", json={})
    assert part.status_code == 200, part.text
    assert part.json()["part"]["cell_id"] == 1

    captured = client.post("/api/training/capture", json={})
    assert captured.status_code == 200, captured.text
    image_id = captured.json()["frame"]["image_id"]
    image = client.get(f"/api/training/images/{image_id}/original")
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"

    saved = client.post(
        "/api/training/annotations",
        json={"image_id": image_id, "annotations": []},
    )
    assert saved.status_code == 200, saved.text

    cells = client.get("/api/training/cells").json()
    assert cells["cells"][0]["cell_id"] == 1
    assert cells["cells"][0]["current"] is True

    moved = client.post("/api/training/cells/move", json={"cell_id": 5})
    # Деталь не завершена — станцию двигать нельзя, это 409.
    assert moved.status_code == 409


def test_follow_pallet_off_keeps_station_still(tmp_path: Path, pallet):
    settings, origin = pallet
    station = FakeStation()
    collector = TrainingCollector(
        TrainingConfig(root_folder=tmp_path / "datasets", follow_pallet=False),
        frame_source=FakeCameras(),
        station=station,
        pallet=settings,
        origin=origin,
    )
    collector.start_session("без движения")
    state = collector.begin_part()
    assert state["part"]["cell_id"] == 1
    assert state["part"]["movement"]["enabled"] is False
    assert station.moves == []
    for _ in range(3):
        collector.capture_next()
        collector.skip_current()
    assert collector.finish_part()["finished_part"]["cell_id"] == 1


def test_rehome_and_manual_move_are_locked_during_part(collector: TrainingCollector):
    collector.start_session("тест")
    collector.begin_part()
    with pytest.raises(CollectorError):
        collector.move_to_cell(10)
    with pytest.raises(CollectorError):
        collector.home()
