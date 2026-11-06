"""Управление планарной станцией через те же функции, что и production.

Мастер обучения не должен знать про G-коды: он вызывает
:func:`project.station.requests.move_to_coordinates` — ту самую функцию,
которой пользуется :func:`project.alghorithms.core.main_algorithm`. Вместе с
ней работает и учёт текущей позиции в ``project/configuration/coordinates.json``,
и расчёт времени перемещения по максимальным скоростям осей.

Импорт ``serial``, ``flet`` и production-модулей выполняется лениво: мастер
должен запускаться и без подключённой станции (``--motion off``), и без
установленного Flet-стека на машине разметки.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable

from project.training.pallet import PalletError, Cell, read_current_coordinates
from project.training.paths import COORDINATES_FILE, production_path


class StationError(RuntimeError):
    """Станция не подключена или перемещение не выполнено."""


@dataclass(frozen=True)
class MoveResult:
    """Результат одного перемещения."""

    moved: bool
    x: float
    y: float
    z: float
    previous: tuple[float, float, float]
    settle_seconds: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "moved": self.moved,
            "x": round(self.x, 3),
            "y": round(self.y, 3),
            "z": round(self.z, 3),
            "previous": [round(value, 3) for value in self.previous],
            "settle_seconds": self.settle_seconds,
        }


class PlanarStation:
    """Подключение к станции и перемещения по координатам паллеты.

    ``enabled=False`` переводит объект в «сухой» режим: координаты
    пересчитываются и записываются, но команды на контроллер не уходят. Это
    нужно для разметки уже снятых кадров и для тестов без оборудования.
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        port: str | None = None,
        baudrate: int = 115200,
        timeout: float = 1.0,
        settle_seconds: float = 0.5,
        coordinates_file: str = COORDINATES_FILE,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.enabled = bool(enabled)
        self.port = port or None
        self.baudrate = int(baudrate)
        self.timeout = float(timeout)
        self.settle_seconds = max(0.0, float(settle_seconds))
        self.coordinates_file = production_path(coordinates_file)
        self._clock = clock
        self._sleep = sleep
        self._lock = threading.RLock()
        self._connection = None
        self._page = None

    # Состояние

    @property
    def connected(self) -> bool:
        connection = self._connection
        try:
            return bool(self.enabled and connection is not None and connection.is_open)
        except Exception:
            return False

    @property
    def position(self) -> tuple[float, float, float]:
        return read_current_coordinates(self.coordinates_file)

    def _safe_position(self) -> tuple[float, float, float] | None:
        """Позиция без исключения: конфигурация может быть ещё не создана."""
        try:
            return self.position
        except PalletError:
            return None

    def status(self) -> dict[str, Any]:
        position = self._safe_position()
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "settle_seconds": self.settle_seconds,
            "position": (
                {
                    "x": round(position[0], 3),
                    "y": round(position[1], 3),
                    "z": round(position[2], 3),
                }
                if position
                else None
            ),
        }

    # Подключение

    def connect(self) -> None:
        """Открыть COM-порт станции (повторный вызов безопасен)."""
        if not self.enabled:
            return
        with self._lock:
            if self.connected:
                return
            try:
                from project.station.connection import establish_connection
            except Exception as exc:  # pragma: no cover - зависит от окружения
                raise StationError(
                    f"Не удалось загрузить модуль подключения станции: {exc}"
                ) from exc
            connection = establish_connection(
                self._page,
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            if connection is None:
                raise StationError(
                    "Станция не найдена: не открылся COM-порт с описанием "
                    "'USB-SERIAL'. Проверьте кабель и питание контроллера "
                    "или запустите мастер с --motion off."
                )
            self._connection = connection

    def close(self) -> None:
        with self._lock:
            connection = self._connection
            self._connection = None
        if connection is None:
            return
        try:
            from project.station.connection import close_connection

            close_connection(connection)
        except Exception:
            try:
                connection.close()
            except Exception:
                pass

    # Перемещения

    def move_to(
        self,
        x: float,
        y: float,
        z: float | None = None,
        *,
        settle: bool = True,
    ) -> MoveResult:
        """Переместить станцию в координаты паллеты.

        Используется production-функция ``move_to_coordinates``: она сама
        отправляет ``G0``, выжидает расчётное время хода и записывает новую
        позицию в ``coordinates.json``.
        """
        try:
            previous = self.position
        except PalletError as exc:
            raise StationError(
                f"Не удалось прочитать текущие координаты станции: {exc}"
            ) from exc
        target_z = previous[2] if z is None else float(z)
        if not self.enabled:
            return MoveResult(
                moved=False,
                x=float(x),
                y=float(y),
                z=target_z,
                previous=previous,
                settle_seconds=0.0,
            )

        self.connect()
        with self._lock:
            connection = self._connection
            if connection is None:
                raise StationError("Нет соединения со станцией")
            try:
                from project.station.requests import move_to_coordinates
            except Exception as exc:  # pragma: no cover - зависит от окружения
                raise StationError(
                    f"Не удалось загрузить функции управления станцией: {exc}"
                ) from exc
            try:
                move_to_coordinates(
                    connection,
                    float(x),
                    float(y),
                    target_z,
                )
            except Exception as exc:
                # Соединение могло разорваться во время хода; следующая
                # попытка начнётся с нового открытия порта.
                self.close()
                raise StationError(f"Перемещение не выполнено: {exc}") from exc

        if settle and self.settle_seconds:
            # Production-цикл после команды ждёт стабилизации кадра
            # (wait_for_processing): без паузы камера успевает отдать кадр
            # с прошлой позиции.
            self._sleep(self.settle_seconds)
        return MoveResult(
            moved=True,
            x=float(x),
            y=float(y),
            z=target_z,
            previous=previous,
            settle_seconds=self.settle_seconds if settle else 0.0,
        )

    def move_to_cell(self, cell: Cell, *, settle: bool = True) -> MoveResult:
        return self.move_to(cell.x, cell.y, cell.z, settle=settle)

    def home(self, *, settle: bool = True) -> MoveResult:
        """Калибровка ``G28`` и парковка — как ``move_to_home`` в production."""
        if not self.enabled:
            return MoveResult(
                moved=False,
                x=0.0,
                y=0.0,
                z=0.0,
                previous=self.position,
                settle_seconds=0.0,
            )
        self.connect()
        with self._lock:
            connection = self._connection
            if connection is None:
                raise StationError("Нет соединения со станцией")
            try:
                from project.station.requests import move_to_home
            except Exception as exc:  # pragma: no cover - зависит от окружения
                raise StationError(
                    f"Не удалось загрузить функции управления станцией: {exc}"
                ) from exc
            try:
                move_to_home(connection)
            except Exception as exc:
                self.close()
                raise StationError(f"Калибровка не выполнена: {exc}") from exc
        if settle and self.settle_seconds:
            self._sleep(self.settle_seconds)
        x, y, z = self.position
        return MoveResult(
            moved=True,
            x=x,
            y=y,
            z=z,
            previous=(0.0, 0.0, 0.0),
            settle_seconds=self.settle_seconds if settle else 0.0,
        )

    def wait(self, seconds: float) -> None:
        """Пауза, используемая мастером между съёмкой и перемещением."""
        if seconds > 0:
            self._sleep(seconds)

    def __enter__(self) -> "PlanarStation":
        self.connect()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()


class ManualMover:
    """Заглушка перемещения: мастер работает от текущей позиции станции."""

    enabled = False

    def status(self) -> dict[str, Any]:
        return {"enabled": False, "connected": False, "position": None}
