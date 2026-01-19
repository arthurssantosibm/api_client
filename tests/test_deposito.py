from unittest.mock import patch, MagicMock

def test_realizar_deposito_sucesso(client):
    with patch("api.execute_routes.get_connection") as mock_conn:
        mock_db = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchone.side_effect = [
            {"id": 1, "saldo_cc": 100},  # busca usuário
            {"saldo_cc": 200}           # saldo atualizado
        ]

        mock_db.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_db

        response = client.post(
            "/deposito",
            json={"email": "user@email.com", "valor": 100},
            headers={"X-Internal-Key": "INTERNAL_SECRET"}
        )

        assert response.status_code == 200
        assert response.json()["saldo_atual"] == 200
