import json
import os
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

import sys
sys.path.insert(0, r'C:\Users\user\Desktop\threecam\project\alghorithms')
from publisher import push_file_to_pc2, sync_unsent_json_files

def protocol_initialisation():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    protocol_path = f"project/configuration/protocols/protocol.json"

    try:
        os.makedirs(os.path.dirname(protocol_path), exist_ok=True)
        data = {'Start time': str(formatted_time)}

        with open(protocol_path, 'w') as file:
            json.dump(data, file)

    except OSError as e:
        print(f"Ошибка: не удалось инициализировать протокол. {e}")


def adding_to_protocol(vert, hor, defect_type):
    protocol_path = f"project/configuration/protocols/protocol.json"
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    try:
        found = False
        with open(protocol_path, 'r') as file:
            existing_data = json.load(file)

        if 'defects' not in existing_data:
            existing_data['defects'] = []

        for item in existing_data['defects']:
            if item["vert"] is vert and item["hor"] is hor:
                item["type"] = defect_type
                item["time"] = formatted_time
                found = True
                break

        if found is False:
            existing_data['defects'].append(
                {"vert": vert, "hor": hor, "type": defect_type, "time": formatted_time})

        with open(protocol_path, 'w') as file:
            json.dump(existing_data, file, indent=4)

    except OSError as e:
        print(f"Ошибка: не удалось внести брак в протокол. {e}")
    except json.JSONDecodeError as je:
        print(f"Ошибка: не удалось декодировать JSON. {je}")


def protocol_finalization():
    protocol_path = f"project/configuration/protocols/protocol.json"
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")

    try:
        with open(protocol_path, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)

        existing_data['Finish time'] = str(formatted_time)

        with open(protocol_path, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)

        new_fname = f"Протокол_{formatted_time}.json"
        new_path = f"project/configuration/protocols/json/{new_fname}"

        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        with open(new_path, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, indent=4, ensure_ascii=False)

        # Excel сохраняем локально
        saving_excel_protocol(new_path)

        # Сначала пробуем догрузить старые JSON, которые раньше не отправились
        try:
            synced_files = sync_unsent_json_files()
            if synced_files:
                print(f"✅ Догружено старых JSON на ПК аналитики: {len(synced_files)}")
        except Exception as e:
            print(f"❌ Ошибка догрузки старых JSON: {e}")

        # Потом отправляем текущий JSON
        try:
            remote_result = push_file_to_pc2(new_path)
            if remote_result:
                print(f"✅ Текущий JSON отправлен на ПК аналитики: {remote_result[0]}")
            else:
                print("⚠️ Текущий JSON сохранён локально, но пока не отправлен на ПК аналитики")
        except Exception as e:
            print(f"❌ Ошибка отправки текущего JSON: {e}")

    except OSError as e:
        print(f"Ошибка: не удалось завершить протокол. {e}")
    except json.JSONDecodeError as je:
        print(f"Ошибка: не удалось декодировать JSON. {je}")
    except Exception as e:
        print(f"Ошибка в protocol_finalization: {e}")



def saving_excel_protocol(json_path):
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"

    ws['A1'] = "Отчет по инспекции корпусов"
    ws['A1'].font = Font(bold=True, size=14)
    ws.merge_cells('A1:F1')
    ws['A1'].alignment = Alignment(horizontal='center')

    ws['A2'] = "Время начала инспекции:"
    ws['B2'] = data["Start time"]

    ws['A3'] = "Время окончания инспекции:"
    ws['B3'] = data["Finish time"]

    total_items = len(data["defects"])
    good_count = sum(1 for item in data["defects"] if item["type"] == "good")
    defective_count = total_items - good_count

    ws['D2'] = "Годных корпусов:"
    ws['E2'] = good_count

    ws['D3'] = "Бракованных корпусов:"
    ws['E3'] = defective_count

    ws['A5'] = ""

    ws['A6'] = "Детальный отчёт"
    ws['A6'].font = Font(bold=True, size=12)
    ws.merge_cells('A6:F6')

    headers = ["Номер корпуса на паллете", "Положение по вертикали",
               "Положение по горизонтали", "Годность корпуса",
               "Причина брака", "Время инспекции"]

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col_num, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')

    defect_type_mapping = {
        "good": "Годен",
        "omission": "Опущение",
        "sinks": "Раковины",
        "platform": "Залив монтажки",
        "contacts": "Залив контактов",
        "flatness": "Неплоскостность",
        "glass": "Стекло",
        "mechanics": "Механика ободка"
    }

    for row_num, item in enumerate(data["defects"], 8):
        ws.cell(row=row_num, column=1, value=row_num - 7)
        ws.cell(row=row_num, column=2, value=item["vert"] + 1)
        ws.cell(row=row_num, column=3, value=item["hor"] + 1)

        if item["type"] == "good":
            ws.cell(row=row_num, column=4, value="Годен")
            ws.cell(row=row_num, column=5, value="Нет")
        else:
            ws.cell(row=row_num, column=4, value="Брак")
            reason = defect_type_mapping.get(item["type"], item["type"])
            ws.cell(row=row_num, column=5, value=reason)

        ws.cell(row=row_num, column=6, value=item["time"])

    for col_num in range(1, 7):
        column_letter = get_column_letter(col_num)
        max_length = 0

        for row_num in range(7, 7 + len(data["defects"]) + 1):
            cell_value = ws.cell(row=row_num, column=col_num).value
            if cell_value:
                max_length = max(max_length, len(str(cell_value)))

        adjusted_width = max_length + 2
        ws.column_dimensions[column_letter].width = adjusted_width

    for row_num in range(8, 8 + len(data["defects"])):
        for col_num in range(1, 7):
            cell = ws.cell(row=row_num, column=col_num)
            cell.alignment = Alignment(horizontal='center')

    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    output_fname = f"Отчет_{formatted_time}.xlsx"
    output_path = f"project/configuration/protocols/excel/{output_fname}"
    wb.save(output_path)