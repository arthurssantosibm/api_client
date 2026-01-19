from unittest.mock import patch, MagicMock

def test_update_usuario_com_senha(client):
    with patch("api.execute_routes.get_connection") as mock_conn:
        mock_db = MagicMock()
        mock_cursor = MagicMock()

        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {"id": 1}
        mock_conn.return_value = mock_db

        response = client.put(
            "/updateUsuarios/1",
            json={
                "nome": "Novo Nome",
                "email": "novo@email.com",
                "telefone": "11999999999",
                "senha": "nova123"
            }
        )

        assert response.status_code == 200
        assert "sucesso" in response.json()["message"].lower()
