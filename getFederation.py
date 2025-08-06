def get_user_federation_id(access_token, realm_name):
    """Возвращает ID первого провайдера User Federation в реалме"""
    url = f"http://keycloak-server/auth/admin/realms/{realm_name}/components?type=org.keycloak.storage.UserStorageProvider"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        federations = response.json()
        if federations:
            return federations[0]["id"]  # Берём первый провайдер
        else:
            raise Exception("User Federation не найдена!")
    else:
        raise Exception(f"Ошибка: {response.status_code}")
