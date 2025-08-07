def create_client_scope_with_mapper(access_token, realm_name, mapper_data):
    """
    Создает Client Scope с User Attribute Protocol Mapper
    
    :param access_token: токен администратора
    :param realm_name: название реалма
    :param mapper_data: данные маппера из Excel
    """
    # 1. Создаем Client Scope
    scope_url = f"http://keycloak-server/auth/admin/realms/{realm_name}/client-scopes"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Основные настройки Client Scope
    scope_payload = {
        "name": f"{mapper_data['ad_attribute']}_scope",
        "description": f"Scope for {mapper_data['ad_attribute']} attribute",
        "protocol": "openid-connect",
        "attributes": {
            "include.in.token.scope": "true",
            "display.on.consent.screen": "true",
            "gui.order": "1"  # Порядок отображения в интерфейсе
        }
    }
    
    try:
        # Создаем Client Scope
        response = requests.post(scope_url, json=scope_payload, headers=headers)
        response.raise_for_status()
        scope_id = response.json()["id"]
        print(f"Client Scope создан: {mapper_data['ad_attribute']}_scope (ID: {scope_id})")
        
        # 2. Добавляем Protocol Mapper типа User Attribute
        mapper_url = f"{scope_url}/{scope_id}/protocol-mappers/models"
        
        mapper_payload = {
            "name": f"{mapper_data['ad_attribute']}_mapper",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",  # Тип User Attribute
            "config": {
                "user.attribute": mapper_data["ad_attribute"],
                "claim.name": mapper_data["token_attribute"],
                "jsonType.label": "String",
                "id.token.claim": str(mapper_data["id_token"]).lower(),
                "access.token.claim": str(mapper_data["access_token"]).lower(),
                "userinfo.token.claim": str(mapper_data["user_info"]).lower(),
                "multivalued": "false"  # Для атрибутов с множественными значениями
            }
        }
        
        # Создаем Protocol Mapper
        response = requests.post(mapper_url, json=mapper_payload, headers=headers)
        if response.status_code == 201:
            print(f"User Attribute Mapper создан для {mapper_data['ad_attribute']}")
        else:
            print(f"Ошибка при создании Mapper: {response.text}")
    
    except Exception as e:
        print(f"Ошибка: {str(e)}")
