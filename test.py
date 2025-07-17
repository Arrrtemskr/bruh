import os
import shutil
from pathlib import Path

def copy_directories(source_dir, target_dir, directories_to_copy):
    """
    Копирует указанные директории из source_dir в target_dir.
    
    :param source_dir: Путь к исходной директории (где ищем директории для копирования)
    :param target_dir: Путь к целевой директории (куда копируем)
    :param directories_to_copy: Список названий директорий для копирования
    """
    # Создаем целевую директорию, если она не существует
    Path(target_dir).mkdir(parents=True, exist_ok=True)
    
    # Получаем список всех поддиректорий в исходной директории
    existing_dirs = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
    
    # Копируем только те директории, которые есть в обоих списках
    for dir_name in directories_to_copy:
        if dir_name in existing_dirs:
            src_path = os.path.join(source_dir, dir_name)
            dst_path = os.path.join(target_dir, dir_name)
            
            # Удаляем целевую директорию, если она уже существует
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path)
            
            # Копируем директорию
            shutil.copytree(src_path, dst_path)
            print(f"Директория '{dir_name}' скопирована в '{target_dir}'")
        else:
            print(f"Директория '{dir_name}' не найдена в '{source_dir}'")

if __name__ == "__main__":
    # Настройки
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Директория, где лежит скрипт
    SOURCE_DIR = os.path.join(SCRIPT_DIR, "rules")  # Исходная директория с директориями для копирования
    TARGET_DIR = os.path.join(SCRIPT_DIR, "copied_rules")  # Целевая директория (будет создана)
    
    # Массив с названиями директорий для копирования
    DIRECTORIES_TO_COPY = [
        "dir1",
        "dir2",
        "dir3"
    ]
    
    # Проверяем, существует ли исходная директория
    if not os.path.exists(SOURCE_DIR):
        print(f"Исходная директория '{SOURCE_DIR}' не существует!")
    else:
        copy_directories(SOURCE_DIR, TARGET_DIR, DIRECTORIES_TO_COPY)
