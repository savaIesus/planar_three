from pathlib import Path
import shutil

from win32comext.shell.demos.IShellLinkDataList import console_props

# ПК аналитики для Планар-3(Вместо r"N:\\" можно использовать - r"P:\\")
REMOTE_ROOT = Path(r"N:\\")

# Локальная папка, где хранятся JSON протоколы Планар-3
LOCAL_JSON_DIR = Path(r"project/configuration/protocols/json")

def is_remote_available():
    """
    Проверяет, доступна ли сетевая папка ПК аналитики.
    """
    try:
        return REMOTE_ROOT.exists() and REMOTE_ROOT.is_dir()
    except OSError as e:
        print(f"❌ ПК аналитики недоступен: {e}")
        return False

def push_file_to_pc2(local_path):
    """
    Отправляет один JSON файл на ПК аналитики.
    Если ПК аналитики недоступен, файл остается локально.
    """
    local_path = Path(local_path)

    if local_path.suffix.lower() != ".json":
        print(f"⚠️ Пропускаем не JSON: {local_path.name}")
        return []
    print()

    if not local_path.exists():
        print(f"❌ Локальный файл не найден: {local_path}")
        return []

    if not is_remote_available():
        print("⚠️ ПК аналитики недоступен. JSON сохранён локально и будет отправлен позже.")
        return []

    try:
        remote_path = REMOTE_ROOT / local_path.name

        if remote_path.exists():
            print(f"ℹ️ JSON уже есть на ПК аналитики: {remote_path}")
            return [remote_path]

        shutil.copy2(local_path, remote_path)
        print(f"✅ JSON отправлен на ПК аналитики: {remote_path}")
        return [remote_path]

    except OSError as e:
        print(f"❌ Ошибка отправки JSON на ПК аналитики: {e}")
        print("Файл остался локально и будет отправлен позже.")
        return []

    except Exception as e:
        print(f"❌ Неизвестная ошибка отправки JSON: {e}")
        return []

def sync_unsent_json_files():
    """
    Догружает на ПК аналитики все JSON-файлы из локальной папки,
    которых ещё нет на удалённом ПК.
    """
    sent_files = []

    if not LOCAL_JSON_DIR.exists():
        print(f"⚠️ Локальная папка JSON не найдена: {LOCAL_JSON_DIR}")
        return sent_files

    if not is_remote_available():
        print("⚠️ ПК аналитики недоступен. Догрузка JSON сейчас невозможна.")
        return sent_files

    json_files = sorted(LOCAL_JSON_DIR.glob("*.json"))

    if not json_files:
        print("ℹ️ Локальных JSON для догрузки нет.")
        return sent_files

    for local_json in json_files:
        remote_json = REMOTE_ROOT / local_json.name

        try:
            if remote_json.exists():
                continue

            shutil.copy2(local_json, remote_json)
            sent_files.append(remote_json)
            print(f"✅ Догружен JSON на ПК аналитики: {remote_json}")

        except OSError as e:
            print(f"❌ Не удалось догрузить JSON {local_json.name}: {e}")
            break

        except Exception as e:
            print(f"❌ Неизвестная ошибка при догрузке {local_json.name}: {e}")
            break

    if sent_files:
        print(f"✅ Догрузка завершена. Отправлено файлов: {len(sent_files)}")
    else:
        print("ℹ️ Новых JSON для отправки нет.")

    return sent_files