import requests
import openpyxl
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Конфигурация Keycloak
KEYCLOAK_URL = "http://keycloak-server/auth"  # Замените на ваш URL Keycloak
REALM_NAME = "master"  # Реалм для авторизации (обычно master для админских операций)
ADMIN_USERNAME = "admin"  # Логин администратора
ADMIN_PASSWORD = "password"  # Пароль администратора
CLIENT_ID = "admin-cli"  # Клиент для админских операций

# Настройка ретраев для запросов
session = requests.Session()
retry = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

def get_admin_token():
    """Получение access token для администратора Keycloak"""
    token_url = f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token"
    payload = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
        "client_id": CLIENT_ID,
        "grant_type": "password"
    }
    
    try:
        response = session.post(token_url, data=payload)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Ошибка при получении токена: {e}")
        raise

def create_keycloak_admin_client(token):
    """Создание клиента для работы с Keycloak Admin API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    return {
        "get": lambda url: session.get(f"{KEYCLOAK_URL}/admin/{url}", headers=headers),
        "post": lambda url, json: session.post(f"{KEYCLOAK_URL}/admin/{url}", json=json, headers=headers),
        "put": lambda url, json: session.put(f"{KEYCLOAK_URL}/admin/{url}", json=json, headers=headers),
        "delete": lambda url: session.delete(f"{KEYCLOAK_URL}/admin/{url}", headers=headers)
    }

def create_mappers_and_scopes(excel_path, target_realm):
    """Основная функция для создания мапперов и client scopes"""
    try:
        # 1. Получаем токен
        print("Получение токена администратора...")
        token = get_admin_token()
        
        # 2. Создаем клиент для работы с API
        kc_admin = create_keycloak_admin_client(token)
        
        # 3. Загружаем Excel файл
        print("Чтение Excel файла...")
        wb = openpyxl.load_workbook(excel_path)
        sheet = wb.active
        
        # 4. Получаем список user federations в целевом реалме
        print(f"Поиск user federations в реалме {target_realm}...")
        response = kc_admin["get"](f"realms/{target_realm}/components?parent={target_realm}&type=org.keycloak.storage.UserStorageProvider")
        response.raise_for_status()
        user_federations = response.json()
        
        if not user_federations:
            print(f"В реалме {target_realm} не найдено user federations")
            return
        
        # Берем первую user federation (можно добавить логику выбора конкретной)
        user_federation = user_federations[0]
        user_federation_id = user_federation["id"]
        print(f"Найдена user federation: {user_federation['name']} (ID: {user_federation_id})")
        
        # 5. Обрабатываем строки Excel
        for row in sheet.iter_rows(min_row=2, values_only=True):
            (
                mapper_num, ad_attribute_name, description, 
                token_attribute_name, id_token, access_token, user_info
            ) = row
            
            # Пропускаем пустые строки
            if not ad_attribute_name:
                continue
            
            print(f"\nОбработка маппера: {ad_attribute_name}")
            
            # 6. Создаем маппер в user federation
            mapper_config = {
                "name": ad_attribute_name,
                "providerId": "user-attribute-ldap-mapper",
                "providerType": "org.keycloak.storage.ldap.mappers.LDAPStorageMapper",
                "parentId": user_federation_id,
                "config": {
                    "user.model.attribute": [ad_attribute_name],
                    "ldap.attribute": [ad_attribute_name],
                    "read.only": ["true"],
                    "always.read.value.from.ldap": ["true"],
                    "is.mandatory.in.ldap": ["false"]
                }
            }
            
            try:
                response = kc_admin["post"](f"realms/{target_realm}/components", json=mapper_config)
                response.raise_for_status()
                print(f"Маппер {ad_attribute_name} создан")
            except Exception as e:
                print(f"Ошибка при создании маппера {ad_attribute_name}: {e}")
                continue
            
            # 7. Создаем client scope
            scope_config = {
                "name": f"{ad_attribute_name}_scope",
                "description": description,
                "protocol": "openid-connect",
                "attributes": {
                    "include.in.token.scope": "true",
                    "display.on.consent.screen": "true"
                },
                "protocolMappers": [{
                    "name": f"{ad_attribute_name}_mapper",
                    "protocol": "openid-connect",
                    "protocolMapper": "oidc-usermodel-attribute-mapper",
                    "config": {
                        "user.attribute": ad_attribute_name,
                        "claim.name": token_attribute_name,
                        "jsonType.label": "String",
                        "id.token.claim": str(id_token).lower(),
                        "access.token.claim": str(access_token).lower(),
                        "userinfo.token.claim": str(user_info).lower()
                    }
                }]
            }
            
            try:
                response = kc_admin["post"](f"realms/{target_realm}/client-scopes", json=scope_config)
                response.raise_for_status()
                print(f"Client scope для {ad_attribute_name} создан")
            except Exception as e:
                print(f"Ошибка при создании client scope для {ad_attribute_name}: {e}")
        
        print("\nГотово!")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")

# Пример использования
if __name__ == "__main__":
    excel_file = "mappers.xlsx"  # Путь к вашему Excel файлу
    target_realm = "your_target_realm"  # Реалм, в котором нужно создать мапперы
    
    create_mappers_and_scopes(excel_file, target_realm)
