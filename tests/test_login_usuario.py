def test_login_usuario_valido(client):
    # Precisamos enviar o cabeçalho que a API está exigindo
    headers = {"X-Internal-Key": "INTERNAL_SECRET"} # Substitua pelo valor real
    
    response = client.post(
        "/loginUsuarios",
        json={
            "email": "diego@email.com",
            "senha": "@Digs2790"
        },
        headers=headers  # Adicionado aqui
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data