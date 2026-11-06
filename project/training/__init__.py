"""Сбор датасета для ручной разметки дефектов и обучения YOLO.

Модуль намеренно отделён от производственного цикла: он не запускает модели
и не меняет ``PartArchive``/протокол. Но двигается он по проекту так же, как
production-программа: планарная станция встаёт на координаты ячеек паллеты
по маршруту «змейкой» (:mod:`project.training.pallet`), камеры снимаются через
OpenCV-потоки проекта (:mod:`project.training.cameras`), а перемещение выполняется
функциями ``project.station.requests`` (:mod:`project.training.station`).

Мастер можно запустить отдельно (``python -m training``) или подключить к
другому интерфейсу через :class:`TrainingCollector` и
:func:`project.training.server.create_app`.
"""

from project.training.cameras import (
    DEFAULT_CAMERA_ROLES,
    CameraError,
    ProjectCameraSource,
)
from project.training.collector import (
    DEFAULT_DEFECT_CLASSES,
    BoundingBox,
    CameraFrameSource,
    CollectorCameraSource,
    CollectorError,
    FrameRecord,
    TrainingCollector,
    TrainingConfig,
    TrainingDatasetCollector,
    TrainingDatasetStore,
    ValidationError,
)
from project.training.pallet import (
    Cell,
    PalletError,
    PalletOrigin,
    PalletSettings,
    build_route,
    cell_coordinates,
    row_column,
)
from project.training.paths import REPO_ROOT, ensure_project_root
from project.training.station import (
    ManualMover,
    MoveResult,
    PlanarStation,
    StationError,
)
from project.training.yolo import (
    PolygonAnnotation,
    YoloExport,
    export_yolo_dataset,
)

__all__ = [
    "DEFAULT_CAMERA_ROLES",
    "DEFAULT_DEFECT_CLASSES",
    "BoundingBox",
    "CameraError",
    "CameraFrameSource",
    "Cell",
    "CollectorCameraSource",
    "CollectorError",
    "FrameRecord",
    "ManualMover",
    "MoveResult",
    "PalletError",
    "PalletOrigin",
    "PalletSettings",
    "PlanarStation",
    "PolygonAnnotation",
    "ProjectCameraSource",
    "REPO_ROOT",
    "StationError",
    "TrainingCollector",
    "TrainingConfig",
    "TrainingDatasetCollector",
    "TrainingDatasetStore",
    "ValidationError",
    "YoloExport",
    "build_route",
    "cell_coordinates",
    "ensure_project_root",
    "export_yolo_dataset",
    "row_column",
]
