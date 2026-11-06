import json
from collections import defaultdict, Counter
import os
from datetime import datetime
from flet import *
from flet.core.canvas.color import Color

from project.application.addition.colors import color_mode
from project.application.addition.info_page import info_page


def parse_today_protocols():
    today = datetime.now().strftime("%Y-%m-%d")
    protocols_dir = "project/configuration/protocols/json"

    total_stats = defaultdict(int)
    total_records_all_files = 0
    files_processed = 0

    if not os.path.exists(protocols_dir):
        print(f"Директория {protocols_dir} не существует")
        return

    for filename in os.listdir(protocols_dir):
        if filename.startswith("Протокол_") and filename.endswith(".json") and today in filename:
            file_path = os.path.join(protocols_dir, filename)

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                defects = data.get('defects', [])

                file_counter = Counter()
                for defect in defects:
                    defect_type = defect.get('type', 'unknown')
                    file_counter[defect_type] += 1

                for defect_type, count in file_counter.items():
                    total_stats[defect_type] += count

                file_total = len(defects)
                total_records_all_files += file_total
                files_processed += 1

                print(f"\nФайл: {filename}")
                print(f"  Всего записей: {file_total}")
                print(f"  По типам:")
                for defect_type, count in sorted(file_counter.items()):
                    print(f"    {defect_type}: {count}")

            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")

    print(f"Обработано файлов: {files_processed}")
    print(f"Общее количество записей во всех файлах: {total_records_all_files}")
    print(f"Суммарная статистика по типам дефектов:")
    for defect_type, count in sorted(total_stats.items()):
        percentage = (count / total_records_all_files * 100) if total_records_all_files > 0 else 0
        print(f"  {defect_type}: {count} ({percentage:.1f}%)")

    return total_records_all_files, total_stats


def create_pie_chart_sections(total_records, total_stats):
    color_map = {
        'good': colors.GREEN,
        'glass': "#f07832",
        'flatness': "#c89b00",
        'sinks': "#0096ff"
    }

    filtered_stats = {k: v for k, v in total_stats.items() if k != 'good'}
    sorted_stats = sorted(filtered_stats.items(), key=lambda x: x[1], reverse=True)

    sections = []
    total_defects = total_records - total_stats.get("good", 0)

    for defect_type, count in sorted_stats:
        if total_defects > 0:
            percentage = (count / total_defects * 100)
            color = color_map.get(defect_type, colors.GREY)
            section = PieChartSection(
                value=percentage,
                color=color,
                radius=96,
                title=f"{percentage:.1f}%",
                title_style=TextStyle(
                    size=14,
                    weight=FontWeight.BOLD,
                    color=colors.WHITE
                )
            )
            sections.append(section)

    return sections


def create_pie_chart_container(total_records, total_stats):
    sections = create_pie_chart_sections(total_records, total_stats)

    reason_chart = PieChart(
        sections=sections,
        sections_space=1,
        center_space_radius=32,
    )

    return Container(
        width=288,
        height=288,
        content=reason_chart
    )


def create_stats_layer():
    application_colors = color_mode()
    total_records, total_stats = parse_today_protocols()

    total_schemes = TextField(
        label="Корпусов проверено",
        keyboard_type=KeyboardType.NUMBER,
        read_only=True,
        width=192,
        border_radius=16,
        value=str(total_records),
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    good_schemes = TextField(
        label="Годных корпусов",
        keyboard_type=KeyboardType.NUMBER,
        read_only=True,
        width=192,
        border_radius=16,
        value=str(total_stats["good"]),
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    defective_schemes = TextField(
        label="Бракованных корпусов",
        keyboard_type=KeyboardType.NUMBER,
        read_only=True,
        width=192,
        border_radius=16,
        value=str(total_records - total_stats["good"]),
        text_style=TextStyle(color=application_colors["text"]),
        bgcolor=application_colors["inactive"],
        border_color=application_colors["text"],
        focused_border_color=application_colors["active"],
        label_style=TextStyle(color=application_colors["text"])
    )

    upper_row = Row(
        controls=[
            total_schemes,
            Container(width=64),
            defective_schemes,
            Container(width=64),
            good_schemes
        ],
        alignment=MainAxisAlignment.CENTER
    )

    reason_container = create_pie_chart_container(total_records, total_stats)
    info = info_page()

    lower_row = Row(
        controls=[
            reason_container,
            Container(width=32),
            info
        ],
        alignment=MainAxisAlignment.CENTER
    )

    def refresh_data(e):
        new_records, new_stats = parse_today_protocols()

        total_schemes.value = str(new_records)
        good_schemes.value = str(new_stats.get("good", 0))
        defective_schemes.value = str(new_records - new_stats.get("good", 0))
        new_sections = create_pie_chart_sections(new_records, new_stats)
        reason_container.content.sections = new_sections

        e.page.update()

    refresh_button = ElevatedButton(
        text="Обновить статистику",
        icon=icons.REFRESH,
        on_click=refresh_data,
        style=ButtonStyle(
            color=colors.WHITE,
            bgcolor=colors.BLUE_400,
            padding=20,
        )
    )

    return Tab(
        text="Статистика",
        content=Column(
            controls=[
                Container(
                    content=Column(
                        controls=[
                            Container(height=32),
                            Row(
                              controls=[
                                  Container(
                                      width=700,
                                      height=32
                                  ),
                                  Text(
                                      "Отчёт по результатам инспекции изделий",
                                      size=20,
                                      color=application_colors["text"],
                                      weight=FontWeight.BOLD,
                                      text_align=TextAlign.CENTER
                                  ),
                                  Container(
                                      width=700,
                                      height=32
                                  )
                              ]
                            ),
                            Container(height=32),
                            upper_row,
                            Container(height=32),
                            lower_row,
                            Container(height=32),
                            refresh_button,
                            Container(height=32)
                        ]
                    ),
                    padding=20,
                    border=border.all(3),
                    border_radius=border_radius.all(10),
                    width=1900,
                    margin=margin.only(left=20, top=20, right=20, bottom=10),
                )
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER
        ),
    )
