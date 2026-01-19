from unittest.mock import patch, MagicMock

def test_update_usuario_nao_encontrado(client):
    with patch("api.execute_routes.get_connection") as mock_conn:
        mock_db = MagicMock()
        mock_cursor = MagicMock()

        mock_db.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value = mock_db

        response = client.put(
            "/updateUsuarios/99",
            json={"nome": "X", "email": "x@x.com", "telefone": "1"}
        )

        assert response.status_code == 404
