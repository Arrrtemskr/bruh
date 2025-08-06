import openpyxl
from pprint import pprint

def parse_excel_mappers(file_path):
    """
    Парсинг Excel файла с мапперами для Keycloak
    Возвращает список словарей с данными мапперов
    """
    try:
        # Открываем файл Excel
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        
        # Проверяем заголовки (опционально)
        headers = [cell.value for cell in sheet[1]]
        expected_headers = [
            "Маппер №",
            "Название атрибута в AD",
            "Расшифровка",
            "Название атрибута для токена",
            "ID token",
            "Access token",
            "User info"
        ]
        
        if headers != expected_headers:
            print("Предупреждение: структура файла не соответствует ожидаемой!")
            print(f"Ожидалось: {expected_headers}")
            print(f"Получено: {headers}")
        
        # Собираем данные из строк
        mappers = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            # Пропускаем пустые строки
            if not any(row):
                continue
                
            # Распаковываем значения
            (
                mapper_num, 
                ad_attribute, 
                description, 
                token_attribute, 
                id_token, 
                access_token, 
                user_info
            ) = row
            
            # Проверяем обязательные поля
            if not ad_attribute or not token_attribute:
                print(f"Пропуск строки {mapper_num}: отсутствует обязательное поле")
                continue
            
            # Преобразуем булевы значения из Excel (могут быть как строками, так и bool)
            def to_bool(value):
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'y', 'да')
            
            mapper_data = {
                "mapper_num": mapper_num,
                "ad_attribute": ad_attribute,
                "description": description,
                "token_attribute": token_attribute,
                "id_token": to_bool(id_token),
                "access_token": to_bool(access_token),
                "user_info": to_bool(user_info)
            }
            
            mappers.append(mapper_data)
        
        return mappers
        
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None

# Пример использования
if __name__ == "__main__":
    excel_file = "mappers.xlsx"  # Укажите путь к вашему файлу
    
    # Парсим данные
    mappers_data = parse_excel_mappers(excel_file)
    
    # Выводим результат
    if mappers_data:
        print("Успешно распарсено мапперов:", len(mappers_data))
        print("\nПример данных первого маппера:")
        pprint(mappers_data[0])
        
        print("\nВсе мапперы:")
        for idx, mapper in enumerate(mappers_data, 1):
            print(f"\nМаппер #{idx}:")
            print(f"  Атрибут в AD: {mapper['ad_attribute']}")
            print(f"  Описание: {mapper['description']}")
            print(f"  Атрибут в токене: {mapper['token_attribute']}")
            print(f"  В ID token: {mapper['id_token']}")
            print(f"  В Access token: {mapper['access_token']}")
            print(f"  В User info: {mapper['user_info']}")
    else:
        print("Не удалось распарсить файл")
