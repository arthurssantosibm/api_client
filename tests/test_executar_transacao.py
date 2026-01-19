from unittest.mock import patch, MagicMock

def test_executar_transacao(client):
    with patch("api.execute_routes.get_connection") as mock_conn:
        mock_db = MagicMock()
        mock_cursor = MagicMock()

        mock_db.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_db

        response = client.post(
            "/transacoesUsuarios",
            json={
                "email_origin": "a@a.com",
                "email_destination": "b@b.com",
                "valor": 100,
                "mensagem": "teste",
                "user_origin_id": 1
            },
            headers={"X-Internal-Key": "INTERNAL_SECRET"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
