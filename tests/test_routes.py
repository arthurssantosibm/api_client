import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import mysql.connector

from api.execute_routes import (
    criar_router,
    login_router,
    update_router,
    transacoes_router,
    deposit_router
)

app = FastAPI()
app.include_router(criar_router)
app.include_router(login_router)
app.include_router(update_router)
app.include_router(transacoes_router)
app.include_router(deposit_router)

client = TestClient(app)

INTERNAL_KEY = "INTERNAL_SECRET"


# ============================
# HELPERS
# ============================

def build_db(fetchone=None, rowcount=1):
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


# ============================
# INSERT USUÁRIO – ERROS
# ============================

def test_insert_usuario_mysql_error():
    conn, cursor = build_db()
    cursor.execute.side_effect = mysql.connector.Error(msg="Erro SQL")

    with patch("api.execute_routes.get_connection", return_value=conn):
        response = client.post(
            "/usuarios",
            json={
                "nome": "A",
                "email": "a@a.com",
                "telefone": "1",
                "senha": "123"
            }
        )

    assert response.status_code == 500


def test_insert_usuario_exception_generica():
    with patch(
        "api.execute_routes.get_connection",
        side_effect=Exception("Falha")
    ):
        response = client.post(
            "/usuarios",
            json={
                "nome": "A",
                "email": "a@a.com",
                "telefone": "1",
                "senha": "123"
            }
        )

    assert response.status_code == 500


# ============================
# LOGIN – BRANCHES FALTANTES
# ============================

def test_login_sem_internal_key():
    response = client.post(
        "/loginUsuarios",
        json={"email": "a@a.com", "senha": "123"},
        headers={"X-Internal-Key": "ERRADO"}
    )

    assert response.status_code == 403


# ============================
# TRANSAÇÃO – MYSQL ERROR
# ============================

def test_transacao_mysql_error():
    conn, cursor = build_db()
    cursor.execute.side_effect = mysql.connector.Error("Erro")

    with patch("api.execute_routes.get_connection", return_value=conn):
        response = client.post(
            "/transacoesUsuarios",
            json={
                "email_origin": "a@a.com",
                "email_destination": "b@b.com",
                "valor": 10,
                "mensagem": "x",
                "user_origin_id": 1
            },
            headers={"X-Internal-Key": INTERNAL_KEY}
        )

    assert response.status_code == 500


# ============================
# DEPÓSITO – ERROS REAIS
# ============================

def test_deposito_valor_zero(internal_headers):
    payload = {"email": "x@x.com", "valor": 0}
    response = client.post("/deposito", headers=internal_headers, json=payload)
    # Alterado para 422 pois o Pydantic valida o schema antes da rota
    assert response.status_code == 400



def test_deposito_mysql_error():
    conn, cursor = build_db()
    cursor.execute.side_effect = mysql.connector.Error("Erro")

    with patch("api.execute_routes.get_connection", return_value=conn):
        response = client.post(
            "/deposito",
            json={"email": "a@a.com", "valor": 10},
            headers={"X-Internal-Key": INTERNAL_KEY}
        )

    assert response.status_code == 500

def test_deposito_valor_invalido(internal_headers):
    payload = {"email": "x@x.com", "valor": "texto_invalido"} # Isso causa 422 automático
    res = client.post("/deposito", headers=internal_headers, json=payload)
    assert res.status_code == 422

def test_insert_usuario_erro_generico_total():
    """Força a cobertura do bloco 'except Exception' em execute_routes.py"""
    with patch("api.execute_routes.get_connection") as mock_conn:
        # Simula que a conexão funciona, mas o cursor dispara um erro inesperado
        mock_conn.return_value.cursor.side_effect = RuntimeError("Erro de sistema")
        
        payload = {"nome": "Teste", "email": "e@e.com", "telefone": "1", "senha": "1"}
        response = client.post("/usuarios", json=payload)
        
        assert response.status_code == 500
        assert "Erro interno" in response.json()["detail"]
        
def test_erro_interno_inesperado_execucao():
    """Força a cobertura do bloco 'except Exception' e limpeza de recursos."""
    with patch("api.execute_routes.get_connection") as mock_conn:
        # Simula que a conexão funciona, mas a criação do cursor gera um erro genérico (não MySQL)
        mock_connection_obj = MagicMock()
        mock_connection_obj.cursor.side_effect = RuntimeError("Erro genérico de sistema")
        mock_conn.return_value = mock_connection_obj

        payload = {
            "nome": "Teste", 
            "email": "erro@teste.com", 
            "telefone": "123", 
            "senha": "123"
        }
        
        response = client.post("/usuarios", json=payload)
        
        # Verifica se caiu no bloco 'except Exception' que retorna status 500
        assert response.status_code == 500
        assert "Erro interno" in response.json()["detail"]
        # Garante que o bloco 'finally' tentou fechar a conexão
        mock_connection_obj.close.assert_called()
        
def test_erro_inesperado_execucao_total():
    """Força cobertura do bloco 'except Exception' e limpeza de recursos."""
    with patch("api.execute_routes.get_connection") as mock_conn:
        # Simula que a conexão funciona, mas a criação do cursor gera um erro genérico
        mock_connection_obj = MagicMock()
        mock_connection_obj.cursor.side_effect = RuntimeError("Erro de sistema imprevisto")
        mock_conn.return_value = mock_connection_obj

        payload = {
            "nome": "Erro", 
            "email": "erro@sistema.com", 
            "telefone": "0", 
            "senha": "0"
        }
        
        response = client.post("/usuarios", json=payload)
        
        # Verifica se o status retornado é o 500 do bloco genérico
        assert response.status_code == 500
        assert "Erro interno" in response.json()["detail"]
        # Garante que o bloco finally fechou a conexão mesmo com erro
        mock_connection_obj.close.assert_called()