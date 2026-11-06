# planar_three

Проверка корпусов тремя камерами на планарной станции: приложение Flet
управляет станцией по G-кодам, снимает кадры тремя камерами и ищет дефекты
нейросетями YOLO (ultralytics), результаты попадают в протокол и карту
качества паллеты.

## Структура

| Каталог | Назначение |
| --- | --- |
| `main.py` | запуск рабочего Flet-приложения (`Трёхкамерник.bat`) |
| `project/alghorithms` | обход паллеты «змейкой», распознавание, протокол, отчёт |
| `project/station` | COM-порт станции, G-коды, камеры OpenCV, настройки картинки |
| `project/application` | интерфейс Flet (вкладки, кнопки, статистика) |
| `project/configuration` | `launch.json`, `coordinates.json`, `picture.json` и др. |
| `project/training` | **мастер сбора датасета** для обучения YOLO (см. ниже) |

## Рабочий цикл

1. `main_algorithm` (`project/alghorithms/core.py`) ставит станцию на первую
   ячейку паллеты (`*_coordinate_of_the_first_cell` из `coordinates.json`).
2. Для каждой ячейки: `move_to_coordinates` → снимок трёх камер
   (`project/station/camera/feed.py`) → распознавание → окраска кнопки.
3. Обход «змейкой»: чётные ряды — по возрастанию `X`, нечётные — по
   убыванию; переход между рядами — по `Y` на
   `distance_between_vertical_centers`; шаг в ряду —
   `distance_between_horizontal_centers`.
4. По завершении — протокол, Excel-отчёт и статистика.

## Мастер сбора датасета (`project/training`)

Отдельное веб-приложение для ручной разметки дефектов и подготовки
YOLO-датасета. Оно не запускает модели и не пишет протокол, но двигается и
снимает **точно так же**, как рабочий цикл:

* **Движение — планарной станцией.** «Деталь» здесь — ячейка паллеты
  (один корпус под тремя камерами). Перед съёмкой мастер считает координаты
  ячейки по геометрии `main_algorithm` (`project/training/pallet.py`) и
  вызывает production-функцию
  `project.station.requests.move_to_coordinates` — ту же, что и рабочий цикл.
  Поэтому текущая позиция станции ведётся в
  `project/configuration/coordinates.json`, а время хода считается по тем же
  максимальным скоростям осей. Никакого конвейера и шагов ленты нет.
* **Камеры — production-потоки.** Индексы камер определяет
  `connect_to_cameras()`, кадр проходит через
  `apply_settings_to_frame()` с яркостью/контрастом/фильтрами из
  `picture.json`. Порядок ролей совпадает с порядком камер проекта:
  `near` (0), `far` (1), `middle` (2).
* **Паллета — из `launch.json`.** Число рядов и колонок, шаг между корпусами
  и координаты первой ячейки читаются из той же конфигурации, что и у
  рабочего приложения. Номер корпуса в датасете = номер ячейки в маршруте
  «змейкой», поэтому кадр всегда можно привязать к реальному корпусу.
* **Классы дефектов — из протокола.** Палитра по умолчанию совпадает с
  `defect_type_mapping` в `project/alghorithms/protocols.py`
  (`omission`, `sinks`, `platform`, `contacts`, `flatness`, `glass`,
  `mechanics`, `other`) — обученная модель сразу совместима с отчётом.

### Запуск

```
python -m venv .venv                     # один раз
.venv\Scripts\pip install -r req.txt    # зависимости (flet, ultralytics, fastapi…)
training.bat                             # либо: .venv\Scripts\python.exe -m project.training
```

Мастер открывает `http://127.0.0.1:8010/`. Рабочую программу нужно закрыть:
она занимает те же камеры и COM-порт станции.

Полезные ключи:

| Ключ | Назначение |
| --- | --- |
| `--start-cell N` | первый корпус на паллете (номер ячейки «змейкой») |
| `--motion off` | не двигать станцию (разметка без оборудования) |
| `--serial-port COM5` | явный порт станции вместо автопоиска `USB-SERIAL` |
| `--indices near=0,far=1,middle=2` | сопоставление ролей и индексов камер |
| `--no-picture-settings` | не применять фильтры из `picture.json` |
| `--root training_datasets` | папка наборов изображений |
| `--config training_config.example.json` | свои роли камер и классы дефектов |

### Как работать

1. Создать набор: имя, классы дефектов, номер первого корпуса.
2. «Снять следующий корпус» — станция встаёт на координаты ячейки, мастер
   показывает кадр первой камеры.
3. Обвести дефекты полигонами (или «Дефекта нет») → «Готово» → автоматически
   снимается следующая камера. Так три камеры на корпус.
4. «Завершить корпус» → «Снять следующий корпус». Кнопка «Калибровка
   станции» делает `G28` и парковку, как `move_to_home` в рабочем цикле.
5. Клик по ячейке в сетке паллеты — переставить станцию на её координаты.
6. «Завершить набор» — экспорт структуры `yolo/images|labels/train|val` и
   `dataset.yaml`. Кадры без дефекта сохраняются с пустым label-файлом.

Раскладка набора:

```
training_datasets/<набор>/
├─ images/            оригиналы (как их увидит модель)
├─ annotated/         копии с нарисованными полигонами
├─ labels/            YOLO-разметка
├─ details/part_0001/ ROLE_original.jpg, ROLE_annotated.jpg, ROLE.txt
├─ manifest.jsonl     соответствие кадров, камер и ячеек
├─ session.json       состояние сессии
└─ yolo/              train/val + dataset.yaml
```

### API

`GET /api/training/config`, `GET /api/training/state`,
`GET /api/training/cells`, `POST /api/training/cells/move`,
`POST /api/training/home`, `POST /api/training/session`,
`POST /api/training/classes`, `POST /api/training/parts`,
`POST /api/training/capture`, `POST /api/training/annotations`,
`POST /api/training/skip`, `POST /api/training/parts/finish`,
`POST /api/training/session/finish`, `POST /api/training/export`,
`GET /api/training/images/{id}/{kind}`, `GET /api/training/manifest`.

### Тесты

```
.venv\Scripts\python.exe -m pytest project/training/tests -q
```

Тесты работают без оборудования: камеры и станция подменяются заглушками,
HTTP-слой проверяется через `TestClient`.

## Требования

`req.txt` (Python 3.11+). Для мастера дополнительно нужны `fastapi` и
`uvicorn` — они уже в списке; `pytest` требуется только для тестов.
