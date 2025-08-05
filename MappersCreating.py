import openpyxl
from keycloak import KeycloakAdmin

# Подключение к Keycloak (у вас уже реализовано)
keycloak_admin = KeycloakAdmin(
    server_url="http://keycloak-server/auth/",
    username='admin',
    password='password',
    realm_name='master',
    verify=True
)

def create_mappers_and_scopes(excel_path, realm_name):
    # Загружаем Excel файл
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    
    # Переключаемся на нужный realm
    keycloak_admin.realm_name = realm_name
    
    # Получаем список существующих user federations
    user_federations = keycloak_admin.components.get(realm_name)
    
    # Предполагаем, что у нас есть хотя бы одна user federation
    if not user_federations:
        print(f"No user federations found in realm {realm_name}")
        return
    
    # Берем первую user federation (возможно, нужно уточнить логику выбора)
    user_federation_id = user_federations[0]['id']
    
    # Проходим по строкам Excel, начиная со второй (первая - заголовки)
    for row in sheet.iter_rows(min_row=2, values_only=True):
        (
            mapper_num, ad_attribute_name, description, 
            token_attribute_name, id_token, access_token, user_info
        ) = row
        
        # Создаем маппер
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
            # Создаем маппер в Keycloak
            keycloak_admin.create_component(mapper_config)
            print(f"Created mapper for {ad_attribute_name}")
        except Exception as e:
            print(f"Error creating mapper for {ad_attribute_name}: {e}")
            continue
        
        # Создаем client scope
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
            # Создаем client scope в Keycloak
            keycloak_admin.create_client_scope(scope_config)
            print(f"Created client scope for {ad_attribute_name}")
        except Exception as e:
            print(f"Error creating client scope for {ad_attribute_name}: {e}")

# Пример вызова функции
create_mappers_and_scopes("mappers.xlsx", "your_realm_name")
