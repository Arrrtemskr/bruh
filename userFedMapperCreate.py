import requests

def create_ldap_mapper(access_token, realm_name, user_federation_id, mapper_data):
    """
    Создает LDAP-маппер в Keycloak через REST API.
    
    :param access_token: токен администратора
    :param realm_name: название реалма (например, 'my_realm')
    :param user_federation_id: ID провайдера User Federation
    :param mapper_data: данные маппера из Excel
    """
    url = f"http://keycloak-server/auth/admin/realms/{realm_name}/components"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": mapper_data["ad_attribute"],
        "providerId": "user-attribute-ldap-mapper",
        "providerType": "org.keycloak.storage.ldap.mappers.LDAPStorageMapper",
        "parentId": user_federation_id,
        "config": {
            "user.model.attribute": [mapper_data["ad_attribute"]],
            "ldap.attribute": [mapper_data["ad_attribute"]],
            "read.only": ["true"],
            "always.read.value.from.ldap": ["true"],
            "is.mandatory.in.ldap": ["false"]
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Маппер '{mapper_data['ad_attribute']}' создан!")
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
