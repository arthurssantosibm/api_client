from types import SimpleNamespace
import pytest
import mysql.connector
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from api.jwt import create_access_token
from api.execute_routes import realizar_deposito
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


# -------------------------------
# JWT
# -------------------------------
def test_create_access_token_called():
    with patch("api.jwt.SECRET_KEY", "secret"):
        token = create_access_token({"sub": "1"})
        assert token is not None


# -------------------------------
# USUÁRIO
# -------------------------------
def test_insert_usuario_exception_generica():
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = Exception("Erro inesperado")
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        payload = {
            "nome": "Teste",
            "email": "teste@teste.com",
            "telefone": "11999999999",
            "senha": "123456"
        }

        response = client.post("/usuarios", json=payload)
        assert response.status_code == 500
        assert "Erro interno" in response.json()["detail"]
        conn.rollback.assert_called_once()


def test_insert_usuario_mysql_error():
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = mysql.connector.Error("DB error")
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        payload = {"nome": "x", "email": "x@x.com", "telefone": "1", "senha": "1"}
        res = client.post("/usuarios", json=payload)
        assert res.status_code == 500


# -------------------------------
# LOGIN
# -------------------------------
def test_login_header_invalido():
    payload = {"email": "x@x.com", "senha": "123"}
    response = client.post("/loginUsuarios", headers={"X-Internal-Key": "ERRADO"}, json=payload)
    assert response.status_code == 403


def test_login_conta_inativa(internal_headers):
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 1, "senha": "123", "correntista": 0}
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        payload = {"email": "x@x.com", "senha": "123"}
        res = client.post("/loginUsuarios", headers=internal_headers, json=payload)
        assert res.status_code == 403


# -------------------------------
# UPDATE USUÁRIO
# -------------------------------
def test_update_usuario_sem_senha():
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = {"id": 1}
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        payload = {"nome": "Novo", "email": "novo@email.com", "telefone": "11999999999"}
        response = client.put("/updateUsuarios/1", json=payload)
        assert response.status_code == 200
        conn.commit.assert_called_once()


def test_update_usuario_nao_encontrado():
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        payload = {"nome": "X", "email": "x@x.com", "telefone": "11999999999"}
        response = client.put("/updateUsuarios/99", json=payload)
        assert response.status_code == 404


# -------------------------------
# SUSPENDER / REATIVAR
# -------------------------------
def test_suspender_conta_header_invalido():
    response = client.put("/updateUsuarios/suspender/1", headers={"X-Internal-Key": "ERRADO"})
    assert response.status_code == 403


def test_suspender_conta_sucesso():
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        response = client.put("/updateUsuarios/suspender/1", headers={"X-Internal-Key": "INTERNAL_SECRET"})
        assert response.status_code == 200
        conn.commit.assert_called_once()


def test_reativar_conta_header_invalido():
    response = client.put("/updateUsuarios/reativar_por_email/", headers={"X-Internal-Key": "ERRADO"},
                          json={"email": "x@x.com"})
    assert response.status_code == 403


def test_reativar_email_inexistente(internal_headers):
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.rowcount = 0
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        response = client.put("/updateUsuarios/reativar_por_email/", headers=internal_headers,
                              json={"email": "nao@existe.com"})
        assert response.status_code == 404


def test_reativar_conta_por_email_sucesso(internal_headers):
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.rowcount = 1
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        response = client.put("/updateUsuarios/reativar_por_email/", headers=internal_headers,
                              json={"email": "x@x.com"})
        assert response.status_code == 200
        assert "Conta reativada" in response.json()["message"]


# -------------------------------
# TRANSAÇÕES
# -------------------------------
def test_executar_transacao_header_invalido():
    payload = {"email_origin": "a@a.com", "email_destination": "b@b.com", "valor": 10.0, "mensagem": "teste",
               "user_origin_id": 1}
    response = client.post("/transacoesUsuarios", headers={"X-Internal-Key": "ERRADO"}, json=payload)
    assert response.status_code == 403


def test_transacao_mysql_error(internal_headers):
    payload = {"email_origin": "a@a.com", "email_destination": "b@b.com", "valor": 10.0, "mensagem": "teste",
               "user_origin_id": 1}

    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = mysql.connector.Error("fail")
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        response = client.post("/transacoesUsuarios", headers=internal_headers, json=payload)
        assert response.status_code == 500
        conn.rollback.assert_called_once()


# -------------------------------
# DEPÓSITOS
# -------------------------------
def test_deposito_header_invalido():
    response = client.post("/deposito", headers={"X-Internal-Key": "ERRADO"},
                           json={"email": "x@x.com", "valor": 100})
    assert response.status_code == 403


def test_deposito_valor_zero_400(internal_headers):
    payload = {"email": "teste@teste.com", "valor": 0}
    response = client.post("/deposito", headers=internal_headers, json=payload)
    assert response.status_code == 400


def test_deposito_usuario_nao_encontrado(internal_headers):
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = None
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        payload = {"email": "naoexiste@teste.com", "valor": 100}
        response = client.post("/deposito", headers=internal_headers, json=payload)
        assert response.status_code == 404


def test_realizar_deposito_mysql_error(internal_headers):
    with patch("api.execute_routes.get_connection") as mock_conn:
        conn = MagicMock()
        cursor = MagicMock()
        cursor.execute.side_effect = mysql.connector.Error("DB down")
        conn.cursor.return_value = cursor
        mock_conn.return_value = conn

        payload = {"email": "x@x.com", "valor": 100}
        response = client.post("/deposito", headers=internal_headers, json=payload)
        assert response.status_code == 500
        conn.rollback.assert_called_once()


# -------------------------------
# FIXTURES
# -------------------------------
@pytest.fixture
def internal_headers():
    return {"X-Internal-Key": "INTERNAL_SECRET"}

def test_erro_catastrofico_na_conexao():
    """Força a cobertura do bloco 'except Exception' e limpeza de conexão"""
    with patch("api.execute_routes.get_connection") as mock_conn:
        mock_c = MagicMock()
        # Simula que a conexão existe (if conn: True), mas o cursor quebra (Exception)
        mock_c.cursor.side_effect = Exception("Falha crítica no driver")
        mock_conn.return_value = mock_c

        payload = {"nome": "a", "email": "a@a.com", "telefone": "1", "senha": "1"}
        response = client.post("/usuarios", json=payload)
        
        assert response.status_code == 500
        assert "Erro interno" in response.json()["detail"]
        # Isso garante que o rollback/close do branch genérico seja executado
        mock_c.close.assert_called()