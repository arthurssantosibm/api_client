
from unittest.mock import patch, MagicMock

def test_reativar_conta_por_email(client):
    with patch("api.execute_routes.get_connection") as mock_conn:
        mock_db = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.rowcount = 1
        mock_db.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_db

        response = client.put(
            "/updateUsuarios/reativar_por_email/",
            json={"email": "user@email.com"},
            headers={"X-Internal-Key": "INTERNAL_SECRET"}
        )

        assert response.status_code == 200
