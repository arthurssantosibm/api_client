import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import mysql.connector

from api.execute_routes import deposit_router, saque_router, INTERNAL_KEY
from schemas.schemas import DepositoDBRequest, SaqueDBRequest

app = FastAPI()
app.include_router(deposit_router)
app.include_router(saque_router)

client = TestClient(app)

# =========================
# HELPERS
# =========================

def build_db(fetchone=None, rowcount=1):
    """Cria mock de conexão e cursor"""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone
    cursor.rowcount = rowcount
    conn.cursor.return_value = cursor
    conn.commit.return_value = None
    conn.rollback.return_value = None
    conn.close.return_value = None
    cursor.close.return_value = None
    return conn, cursor

internal_headers = {"X-Internal-Key": INTERNAL_KEY}

# =========================
# TESTES DE DEPÓSITO
# =========================

def test_deposito_sucesso():
    mock_user = {"id": 1, "saldo_cc": 100}
    conn, cursor = build_db(fetchone=mock_user)

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "a@a.com", "valor": 50}
        response = client.post("/deposito", headers=internal_headers, json=payload)

    assert response.status_code == 200
    assert response.json()["saldo_atual"] == 100  # porque mock retorna sempre 100

def test_deposito_usuario_nao_encontrado():
    conn, cursor = build_db(fetchone=None)

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "x@x.com", "valor": 50}
        response = client.post("/deposito", headers=internal_headers, json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado"

def test_deposito_valor_invalido():
    payload = {"email": "x@x.com", "valor": 0}
    response = client.post("/deposito", headers=internal_headers, json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Valor inválido"

def test_deposito_mysql_error():
    conn, cursor = build_db()
    cursor.execute.side_effect = mysql.connector.Error(msg="Erro teste")

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "a@a.com", "valor": 50}
        response = client.post("/deposito", headers=internal_headers, json=payload)

    assert response.status_code == 500
    assert "Erro no banco de dados" in response.json()["detail"]

def test_deposito_erro_generico():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    # Faz o execute lançar um erro genérico
    cursor.execute.side_effect = RuntimeError("Erro genérico")
    
    conn.rollback.return_value = None
    cursor.close.return_value = None
    conn.close.return_value = None

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "a@a.com", "valor": 50}
        response = client.post("/deposito", headers=internal_headers, json=payload)

    assert response.status_code == 500
    assert "Erro interno" in response.json()["detail"]
    conn.rollback.assert_called_once()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()

# =========================
# TESTES DE SAQUE
# =========================

def test_saque_sucesso():
    mock_user = {"id": 1, "saldo_cc": 200}
    conn, cursor = build_db(fetchone=mock_user)

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "a@a.com", "valor": 50}
        response = client.post("/saque", headers=internal_headers, json=payload)

    assert response.status_code == 200
    assert response.json()["saldo_atual"] == 200  # retorna valor mockado

def test_saque_usuario_nao_encontrado():
    conn, cursor = build_db(fetchone=None)

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "x@x.com", "valor": 50}
        response = client.post("/saque", headers=internal_headers, json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado"

def test_saque_valor_invalido():
    payload = {"email": "x@x.com", "valor": 0}
    response = client.post("/saque", headers=internal_headers, json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Valor inválido"

def test_saque_saldo_insuficiente():
    mock_user = {"id": 1, "saldo_cc": 30}
    conn, cursor = build_db(fetchone=mock_user)

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "a@a.com", "valor": 50}
        response = client.post("/saque", headers=internal_headers, json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Saldo insuficiente"

def test_saque_mysql_error():
    conn, cursor = build_db(fetchone={"id": 1, "saldo_cc": 100})
    cursor.execute.side_effect = mysql.connector.Error(msg="Erro teste")

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "a@a.com", "valor": 50}
        response = client.post("/saque", headers=internal_headers, json=payload)

    assert response.status_code == 500
    assert "Erro no banco de dados" in response.json()["detail"]

def test_saque_erro_generico():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    # Faz o execute lançar um erro genérico
    cursor.execute.side_effect = RuntimeError("Erro genérico")
    
    conn.rollback.return_value = None
    cursor.close.return_value = None
    conn.close.return_value = None

    with patch("api.execute_routes.get_connection", return_value=conn):
        payload = {"email": "a@a.com", "valor": 50}
        response = client.post("/saque", headers=internal_headers, json=payload)

    assert response.status_code == 500
    assert "Erro interno" in response.json()["detail"]
    conn.rollback.assert_called_once()
    cursor.close.assert_called_once()
    conn.close.assert_called_once()
