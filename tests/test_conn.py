# tests/test_connection_error.py
import pytest
import importlib
from mysql.connector import Error
from unittest.mock import patch

def test_connection_pool_error_on_import():
    with patch(
        "mysql.connector.pooling.MySQLConnectionPool",
        side_effect=Error("Erro de conexão")
    ):
        with pytest.raises(Error):
            import api.connection
            importlib.reload(api.connection)
