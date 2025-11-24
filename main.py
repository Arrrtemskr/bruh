# main.py
import sys
from parse_eml import extract_realm_config_from_eml

def main():
    if len(sys.argv) != 2:
        print("Использование: python main.py <путь_к_файлу.eml>")
        sys.exit(1)

    eml_file = sys.argv[1]

    try:
        realm_config = extract_realm_config_from_eml(eml_file)
        print("\n" + "="*50)
        print("✅ Конфигурация realm успешно извлечена:")
        print("="*50)
        for key, value in realm_config.items():
            print(f"{key:<25}: {value}")
        print("="*50)

        # Пример: передача в Keycloak (заглушка)
        realm_name = realm_config.get("Название realm")
        if realm_name:
            print(f"\n➡️  Готов к созданию realm: '{realm_name}' в Keycloak")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
