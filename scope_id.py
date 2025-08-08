async def create_client_scope_with_mapper(kc, access_token, realm_name, mapper_data):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    scope_name = f"{mapper_data['ad_attribute']}_scope"
    scope_payload = {
        "name": scope_name,
        "description": f"Scope for {mapper_data['ad_attribute']} attribute",
        "protocol": "openid-connect",
        "attributes": {
            "include.in.token.scope": "false",
            "display.on.consent.screen": "true"
        }
    }
    
    # 1. Создаем Client Scope
    create_path = f"/admin/realms/{realm_name}/client-scopes"
    response = await request(kc, "POST", create_path, headers=headers, json=scope_payload)
    
    # 2. Извлекаем ID из заголовка Location
    if response.status == 201:
        location_header = response.headers.get('Location')
        if location_header:
            scope_id = location_header.split('/')[-1]
            print(f"Client Scope создан. ID: {scope_id}")
            
            # 3. Создаем Protocol Mapper
            mapper_path = f"{create_path}/{scope_id}/protocol-mappers/models"
            mapper_payload = {
                "name": f"{mapper_data['ad_attribute']}_mapper",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "config": {
                    "user.attribute": mapper_data["ad_attribute"],
                    "claim.name": mapper_data["token_attribute"],
                    "jsonType.label": "String",
                    "id.token.claim": str(mapper_data["id_token"]).lower(),
                    "access.token.claim": str(mapper_data["access_token"]).lower(),
                    "userinfo.token.claim": str(mapper_data["user_info"]).lower()
                }
            }
            
            mapper_response = await request(kc, "POST", mapper_path, headers=headers, json=mapper_payload)
            if mapper_response.status == 201:
                print(f"Protocol Mapper успешно создан")
                return True
    
    print("Ошибка при создании Client Scope или Protocol Mapper")
    return False
