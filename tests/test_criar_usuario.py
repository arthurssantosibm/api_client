from unittest.mock import patch, MagicMock

def test_criar_usuario_sucesso(client):

    with patch("api.execute_routes.get_connection") as mock_conn:
        mock_db = MagicMock()
        mock_cursor = MagicMock()

        mock_db.cursor.return_value = mock_cursor

        mock_db.commit.return_value = None
        mock_db.close.return_value = None

        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = None
        mock_cursor.close.return_value = None

        mock_conn.return_value = mock_db

        response = client.post(
            "/usuarios",
            json={
                "nome": "Diego Silva",
                "email": "diego@email.com",
                "telefone": "11929292929",
                "senha": "@Digs2790"
            },
            headers={"X-Internal-Key": "INTERNAL_SECRET"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "success"
