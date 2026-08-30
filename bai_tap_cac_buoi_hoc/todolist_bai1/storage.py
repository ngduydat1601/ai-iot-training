import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "tasks.json")


def ensure_data_file():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, ensure_ascii=False, indent=4)

    return DATA_FILE


def load_tasks():
    file_path = ensure_data_file()
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_tasks(tasks):
    file_path = ensure_data_file()
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(tasks, file, ensure_ascii=False, indent=4)
