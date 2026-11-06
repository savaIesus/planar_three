"""Три камеры станции для мастера сбора датасета.

Мастер берёт кадры не из собственного «захватчика», а из тех же OpenCV
потоков, что и production-приложение:

* :func:`project.station.camera.connection.connect_to_cameras` находит
  доступные индексы камер и открывает ``cv2.VideoCapture``;
* :func:`project.station.camera.frame_settings.apply_settings_to_frame`
  применяет яркость/контраст/фильтры из ``project/configuration/picture.json``.

Благодаря этому учебные кадры выглядят ровно так, как их увидит нейросеть в
рабочем цикле, и не нужно отдельно настраивать камеры.

Порядок ролей совпадает с порядком камер в production-приложении
(``project/station/camera/feed.py`` и ``project/alghorithms/contour.py``):
индекс 0 — ближняя камера (``near``), 1 — дальняя (``far``),
2 — средняя/верхняя (``middle``).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Sequence

# Роли в порядке индексов камер production-проекта.
DEFAULT_CAMERA_ROLES = ("near", "far", "middle")

ROLE_TITLES = {
    "near": "Ближняя камера (индекс 0)",
    "far": "Дальняя камера (индекс 1)",
    "middle": "Верхняя камера (индекс 2)",
}


class CameraError(RuntimeError):
    """Камеры не найдены или кадр не получен."""


def _load_apply_settings():
    """Ленивый импорт production-фильтра кадра.

    ``apply_settings_to_frame`` тянет OpenCV, PIL и JSON-конфигурацию; импорт
    на уровне модуля сделал бы ``import training`` зависимым от этих пакетов.
    """
    from project.station.camera.frame_settings import apply_settings_to_frame

    return apply_settings_to_frame


class ProjectCameraSource:
    """Источник кадров: OpenCV-потоки production-приложения.

    ``indices`` позволяет явно сопоставить роли и индексы камер, если на
    конкретной машине они перечислены в другом порядке. ``use_picture_settings``
    включает те же фильтры картинки, что и рабочий цикл.
    """

    def __init__(
        self,
        *,
        roles: Sequence[str] = DEFAULT_CAMERA_ROLES,
        indices: dict[str, int] | None = None,
        use_picture_settings: bool = True,
        warmup_frames: int = 2,
        read_attempts: int = 5,
    ):
        self.roles = tuple(str(role).strip() for role in roles if str(role).strip())
        if not self.roles:
            raise CameraError("Не задан ни один идентификатор камеры")
        self.indices = {str(key): int(value) for key, (value) in (indices or {}).items()}
        self.use_picture_settings = bool(use_picture_settings)
        self.warmup_frames = max(0, int(warmup_frames))
        self.read_attempts = max(1, int(read_attempts))
        self._lock = threading.RLock()
        self._captures: list[Any] = []
        self._camera_indices: list[int] = []
        self._apply_settings = None
        self._last_error: str | None = None

    # Служебное

    @property
    def opened(self) -> bool:
        return bool(self._captures)

    def status(self) -> dict[str, Any]:
        return {
            "opened": self.opened,
            "roles": list(self.roles),
            "camera_indices": list(self._camera_indices),
            "mapping": self.mapping(),
            "use_picture_settings": self.use_picture_settings,
            "error": self._last_error,
        }

    def mapping(self) -> dict[str, int]:
        """Роль камеры → индекс ``cv2.VideoCapture``."""
        result: dict[str, int] = {}
        for position, role in enumerate(self.roles):
            if role in self.indices:
                result[role] = self.indices[role]
            elif position < len(self._camera_indices):
                result[role] = self._camera_indices[position]
        return result

    # Подключение

    def open(self) -> None:
        """Открыть камеры через production-функцию ``connect_to_cameras``."""
        with self._lock:
            if self.opened:
                return
            try:
                from project.station.camera.connection import (
                    CamerasList,
                    connect_to_cameras,
                )
            except Exception as exc:  # pragma: no cover - зависит от окружения
                raise CameraError(
                    f"Не удалось загрузить модуль камер: {exc}"
                ) from exc

            captures = connect_to_cameras()
            indices = list(getattr(CamerasList, "cams_list", []) or [])
            if not captures:
                self._last_error = "Камеры не найдены"
                raise CameraError(
                    "Камеры не найдены. Проверьте USB-подключение и закройте "
                    "производственную программу: она уже занимает камеры."
                )
            missing = [
                role for role in self.roles if role not in self.mapping_after(indices)
            ]
            self._captures = list(captures)
            self._camera_indices = indices
            if missing:
                self.release()
                self._last_error = "Не хватает камер"
                raise CameraError(
                    "Подключено камер: "
                    f"{len(indices)}, а мастеру нужны: {', '.join(self.roles)}. "
                    "Не найдены: " + ", ".join(missing)
                )
            self._last_error = None
            if self.use_picture_settings and self._apply_settings is None:
                try:
                    self._apply_settings = _load_apply_settings()
                    self._last_error = None
                except Exception as exc:
                    self._apply_settings = None
                    print(
                        "Мастер: не удалось загрузить настройки картинки "
                        f"({exc}); кадры сохраняются без фильтров."
                    )
            self._warmup()

    def mapping_after(self, indices: Sequence[int]) -> dict[str, int]:
        """Сопоставление ролей и индексов без изменения состояния объекта."""
        result: dict[str, int] = {}
        for position, role in enumerate(self.roles):
            if role in self.indices:
                result[role] = self.indices[role]
            elif position < len(indices):
                result[role] = int(indices[position])
        return result

    def release(self) -> None:
        with self._lock:
            for capture in self._captures:
                try:
                    capture.release()
                except Exception:
                    pass
            self._captures = []
            self._camera_indices = []

    # Кадры

    def capture_single(self, role: str):
        """Свежий кадр выбранной роли (BGR, uint8)."""
        with self._lock:
            self.open()
            capture = self._capture_for(role)
            apply_settings = self._apply_settings

        frame = None
        for attempt in range(self.read_attempts):
            try:
                success, frame = capture.read()
            except Exception as exc:
                raise CameraError(f"Ошибка чтения камеры {role}: {exc}") from exc
            if success and frame is not None:
                break
            time.sleep(0.05)
            frame = None
        if frame is None:
            raise CameraError(
                f"Камера {role} не отдала кадр. Проверьте, что она не занята "
                "другим приложением."
            )

        if apply_settings is not None:
            try:
                frame = apply_settings(frame)
            except Exception as exc:
                print(f"Мастер: настройки картинки не применены ({exc})")
        self._last_error = None
        return frame

    def _capture_for(self, role: str):
        mapping = self.mapping()
        if role not in mapping:
            raise CameraError(
                f"Для роли {role} не назначена камера. Доступные роли: "
                + ", ".join(mapping)
            )
        index = mapping[role]
        try:
            position = self._camera_indices.index(index)
        except ValueError as exc:
            raise CameraError(
                f"Камера с индексом {index} не открыта"
            ) from exc
        return self._captures[position]

    def _warmup(self) -> None:
        """Прогреть камеры: первый кадр USB-камеры часто пересвечен."""
        if not self.warmup_frames:
            return
        for capture in self._captures:
            for _ in range(self.warmup_frames):
                try:
                    capture.read()
                except Exception:
                    break

    def __enter__(self) -> "ProjectCameraSource":
        self.open()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.release()


def role_title(role: str) -> str:
    return ROLE_TITLES.get(role, role)
