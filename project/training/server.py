"""Отдельный FastAPI-мастер ручной разметки кадров.

Эндпоинты повторяют логику производства: сессия → ячейка паллеты (станция
встаёт на координаты по маршруту «змейкой») → три камеры → ручная разметка →
экспорт YOLO. Никакого управления конвейером здесь нет: в этом проекте
корпуса стоят на паллете, а движение выполняет планарная станция.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Sequence

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from project.training.collector import (
    CollectorError,
    TrainingCollector,
    TrainingConfig,
    ValidationError,
)
from project.training.pallet import PalletError
from project.training.yolo import export_yolo_dataset

_UI_FOLDER = Path(__file__).parent / "ui"


def create_app(
    collector: TrainingCollector | None = None,
    *,
    frame_source=None,
    station=None,
    config: TrainingConfig | None = None,
) -> FastAPI:
    """Создать независимое приложение мастера обучения.

    Для production-запуска передайте источник кадров (``ProjectCameraSource``)
    через ``frame_source``, а управление станцией — через ``station``
    (``PlanarStation``). В тестах удобно передать уже созданный
    ``TrainingCollector`` с фейковыми зависимостями.
    """
    if collector is None:
        collector = TrainingCollector(
            config or TrainingConfig(),
            frame_source=frame_source,
            station=station,
        )
    else:
        if frame_source is not None:
            collector.frame_source = frame_source
        if station is not None:
            collector.station = station

    app = FastAPI(
        title="Мастер сбора датасета YOLO",
        description=(
            "Съёмка корпусов на паллете тремя камерами станции и ручная "
            "разметка дефектов"
        ),
    )
    app.state.training_collector = collector

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(_UI_FOLDER / "index.html", media_type="text/html")

    app.mount(
        "/static",
        StaticFiles(directory=_UI_FOLDER / "static"),
        name="training-static",
    )

    def current_collector() -> TrainingCollector:
        return app.state.training_collector

    @app.get("/api/training/state")
    async def get_state():
        return JSONResponse(_state_with_urls(current_collector()))

    @app.get("/api/training/config")
    async def get_config():
        item = current_collector()
        station = item.station
        source = item.frame_source
        cameras = (
            source.status()
            if source is not None and hasattr(source, "status")
            else {"opened": False, "mapping": {}}
        )
        return JSONResponse(
            {
                "camera_roles": list(item.config.camera_roles),
                "cameras": cameras,
                "camera_mapping": dict(cameras.get("mapping") or {}),
                "defect_classes": list(item.config.defect_classes),
                "yolo_task": item.config.yolo_task,
                "root_folder": str(item.config.root_folder),
                "stations": (
                    {
                        **station.status(),
                        "following": item.moves_enabled,
                    }
                    if station is not None and hasattr(station, "status")
                    else {"enabled": False, "connected": False, "following": False}
                ),
                "motion_enabled": item.moves_enabled,
                "pallet": item.pallet_payload(),
                "start_cell": item.config.start_cell,
            }
        )

    @app.get("/api/training/cells")
    async def get_cells():
        item = current_collector()
        return JSONResponse(
            {
                "pallet": item.pallet_payload(),
                "cells": item.cells(),
                "station": (
                    item.station.status()
                    if item.station is not None and hasattr(item.station, "status")
                    else {"enabled": False, "connected": False}
                ),
            }
        )

    @app.post("/api/training/cells/move")
    async def move_to_cell(payload: dict[str, Any] | None = None):
        payload = payload or {}
        item = current_collector()
        cell_id = payload.get("cell_id")
        if cell_id is None:
            return _error_response(ValidationError("Не указан cell_id"), 400)
        try:
            await asyncio.to_thread(item.move_to_cell, int(cell_id))
        except ValidationError as exc:
            return _error_response(exc, 400)
        except (CollectorError, PalletError) as exc:
            return _error_response(exc, 409)
        except Exception as exc:
            return _error_response(exc, 500)
        return JSONResponse(_state_with_urls(item))

    @app.post("/api/training/home")
    async def station_home():
        item = current_collector()
        try:
            await asyncio.to_thread(item.home)
        except CollectorError as exc:
            return _error_response(exc, 409)
        except Exception as exc:
            return _error_response(exc, 500)
        return JSONResponse(_state_with_urls(item))

    @app.post("/api/training/session", response_model=None)
    async def start_session(payload: dict[str, Any] | None = None):
        payload = payload or {}
        item = current_collector()
        try:
            await asyncio.to_thread(
                item.start_session,
                _optional_text(payload.get("dataset_name")),
                defect_classes=_list_value(
                    payload.get("defect_classes"), item.config.defect_classes
                ),
                camera_roles=_list_value(
                    payload.get("camera_roles"), item.config.camera_roles
                ),
                start_cell=(
                    int(payload["start_cell"])
                    if payload.get("start_cell") is not None
                    else None
                ),
                follow_pallet=payload.get("follow_pallet"),
            )
        except ValidationError as exc:
            return _error_response(exc, 400)
        except (CollectorError, PalletError) as exc:
            return _error_response(exc, 409)
        return JSONResponse(_state_with_urls(item))

    @app.post("/api/training/classes")
    async def add_class(payload: dict[str, Any] | None = None):
        payload = payload or {}
        item = current_collector()
        try:
            classes = await asyncio.to_thread(
                item.add_defect_class,
                _optional_text(payload.get("class_name")),
            )
        except ValidationError as exc:
            return _error_response(exc, 400)
        except CollectorError as exc:
            return _error_response(exc, 409)
        return JSONResponse(
            {
                "ok": True,
                "defect_classes": classes,
                "state": _state_with_urls(item),
            }
        )

    @app.post("/api/training/parts")
    async def start_part(payload: dict[str, Any] | None = None):
        payload = payload or {}
        item = current_collector()
        cell_id = payload.get("cell_id")
        try:
            await asyncio.to_thread(
                item.begin_part,
                _optional_text(payload.get("label")),
                cell_id=int(cell_id) if cell_id is not None else None,
            )
        except ValidationError as exc:
            return _error_response(exc, 400)
        except (CollectorError, PalletError) as exc:
            return _error_response(exc, 409)
        except Exception as exc:
            return _error_response(exc, 500)
        return JSONResponse(_state_with_urls(item))

    @app.post("/api/training/capture")
    async def capture_next(payload: dict[str, Any] | None = None):
        payload = payload or {}
        item = current_collector()
        try:
            record = await asyncio.to_thread(
                item.capture_next,
                camera_role=_optional_text(payload.get("camera_role")),
            )
        except ValidationError as exc:
            return _error_response(exc, 400)
        except CollectorError as exc:
            return _error_response(exc, 409)
        except Exception as exc:
            return _error_response(exc, 500)
        return JSONResponse(
            {
                "ok": True,
                "frame": _record_with_urls(record),
                "state": _state_with_urls(item),
            }
        )

    @app.post("/api/training/annotations")
    async def save_annotation(payload: dict[str, Any] | None = None):
        payload = payload or {}
        item = current_collector()
        regions = payload.get("annotations")
        if regions is None:
            regions = payload.get("polygons")
        if regions is None:
            regions = payload.get("boxes")
        if regions is None and payload.get("bbox") is not None:
            regions = [{"bbox": payload.get("bbox")}]
        if regions is not None and not isinstance(regions, list):
            field_name = (
                "annotations"
                if payload.get("annotations") is not None
                else "polygons"
                if payload.get("polygons") is not None
                else "boxes"
            )
            return _error_response(
                ValidationError(f"{field_name} должен быть списком областей"),
                400,
            )
        # image_id принимается для понятного контракта API, но разметка всегда
        # проверяется относительно current_frame_id: нельзя случайно записать
        # область в предыдущий кадр при двойном клике интерфейса.
        expected_id = item.current_frame_id
        if payload.get("image_id") is not None and expected_id != int(payload["image_id"]):
            return _error_response(
                CollectorError("Кадр уже изменился; обновите текущий экран"),
                409,
            )
        try:
            record = await asyncio.to_thread(
                item.annotate_current,
                defect_class=_optional_text(payload.get("defect_class")),
                annotations=regions or (),
            )
        except ValidationError as exc:
            return _error_response(exc, 400)
        except CollectorError as exc:
            return _error_response(exc, 409)
        return JSONResponse(
            {
                "ok": True,
                "frame": _record_with_urls(record),
                "state": _state_with_urls(item),
            }
        )

    @app.post("/api/training/skip")
    async def skip_annotation(payload: dict[str, Any] | None = None):
        item = current_collector()
        expected_id = item.current_frame_id
        if (
            payload
            and payload.get("image_id") is not None
            and expected_id != int(payload["image_id"])
        ):
            return _error_response(
                CollectorError("Кадр уже изменился; обновите текущий экран"),
                409,
            )
        try:
            record = await asyncio.to_thread(item.skip_current)
        except CollectorError as exc:
            return _error_response(exc, 409)
        return JSONResponse(
            {
                "ok": True,
                "frame": _record_with_urls(record),
                "state": _state_with_urls(item),
            }
        )

    @app.post("/api/training/parts/finish")
    async def finish_part():
        item = current_collector()
        try:
            result = await asyncio.to_thread(item.finish_part)
        except CollectorError as exc:
            return _error_response(exc, 409)
        except Exception as exc:
            return _error_response(exc, 500)
        return JSONResponse(_json_safe(result))

    @app.post("/api/training/session/finish")
    async def finish_session(payload: dict[str, Any] | None = None):
        payload = payload or {}
        item = current_collector()
        try:
            result = await asyncio.to_thread(
                item.finish_session,
                go_home=bool(payload.get("go_home")),
            )
        except CollectorError as exc:
            return _error_response(exc, 409)
        except Exception as exc:
            return _error_response(exc, 500)
        return JSONResponse(_json_safe(result))

    @app.post("/api/training/export")
    async def export_dataset():
        item = current_collector()
        if item.store is None:
            return _error_response(
                CollectorError("Сначала создайте сессию обучения"),
                409,
            )
        try:
            result = await asyncio.to_thread(
                export_yolo_dataset,
                item.store,
                validation_ratio=item.config.validation_ratio,
            )
        except Exception as exc:
            return _error_response(exc, 400)
        return JSONResponse({"ok": True, "yolo": result.to_dict()})

    @app.get("/api/training/images/{image_id}/{kind}")
    async def get_image(image_id: int, kind: str):
        if kind not in (
            "original",
            "annotated",
            "detail_original",
            "detail_annotated",
        ):
            raise HTTPException(400, "Недопустимый тип изображения")
        item = current_collector()
        try:
            path = await asyncio.to_thread(item.image_path, image_id, kind)
        except CollectorError as exc:
            raise HTTPException(404, str(exc)) from exc
        return FileResponse(
            path,
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )

    @app.get("/api/training/manifest")
    async def get_manifest():
        item = current_collector()
        if item.store is None:
            return JSONResponse({"frames": [], "parts": []})
        return JSONResponse(
            {
                "frames": [record.to_dict() for record in item.store.get_frames()],
                "parts": item.store.get_parts(),
            }
        )

    return app


def _record_with_urls(record) -> dict[str, Any]:
    data = record.to_dict()
    data["original_url"] = f"/api/training/images/{record.image_id}/original"
    if record.annotated:
        data["annotated_url"] = f"/api/training/images/{record.image_id}/annotated"
    return data


def _state_with_urls(collector: TrainingCollector) -> dict[str, Any]:
    state = collector.snapshot()
    frame = state.get("current_frame")
    if isinstance(frame, dict):
        image_id = frame.get("image_id")
        if image_id is not None:
            frame["original_url"] = f"/api/training/images/{image_id}/original"
            if frame.get("annotated"):
                frame["annotated_url"] = (
                    f"/api/training/images/{image_id}/annotated"
                )
    return state


def _list_value(value: Any, default: Sequence[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raise ValidationError("Значение должно быть списком или строкой через запятую")


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _error_response(exc: Exception, status_code: int) -> JSONResponse:
    return JSONResponse(
        {"ok": False, "error": str(exc), "type": type(exc).__name__},
        status_code=status_code,
    )


def _json_safe(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    return value
