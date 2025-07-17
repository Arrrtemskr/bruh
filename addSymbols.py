def process_file(input_file, output_file):
    """
    Обрабатывает файл, добавляя кавычки и запятую к каждой строке.
    
    :param input_file: Путь к исходному файлу
    :param output_file: Путь к выходному файлу
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                # Удаляем лишние пробелы и переносы строк
                cleaned_line = line.strip()
                if cleaned_line:  # Если строка не пустая
                    # Добавляем кавычки и запятую
                    processed_line = f'"{cleaned_line}",\n'
                    outfile.write(processed_line)
            
        print(f"Файл успешно обработан. Результат сохранен в {output_file}")
    
    except FileNotFoundError:
        print(f"Ошибка: файл {input_file} не найден!")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    # Настройки
    INPUT_FILE = "input.txt"  # Имя исходного файла
    OUTPUT_FILE = "output.txt"  # Имя выходного файла
    
    # Запускаем обработку
    process_file(INPUT_FILE, OUTPUT_FILE)
