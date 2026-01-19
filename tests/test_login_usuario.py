def test_login_usuario_valido(client):
    headers = {"X-Internal-Key": "INTERNAL_SECRET"}
    
    response = client.post(
        "/loginUsuarios",
        json={
            "email": "diego@email.com",
            "senha": "@Digs2790"
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data