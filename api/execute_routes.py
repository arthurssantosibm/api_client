from fastapi import APIRouter, HTTPException
from api.connection import get_connection
from schemas.schemas import CriarConta
import mysql.connector # Importado para capturar erros específicos

# 1. Ajuste no prefixo: Se o prefixo é "/usuarios", a rota abaixo se torna "/usuarios/usuarios"
# Geralmente, deixamos o prefixo como "/usuarios" e o path como "/" ou apenas ""
criar_router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@criar_router.post("/") # Alterado de "/usuarios" para "/" para evitar URL duplicada
async def insert_usuario(data: CriarConta):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, telefone, senha)
            VALUES (%s, %s, %s, %s)
            """,
            (
                data.nome,
                data.email,
                data.telefone,
                data.senha
            )
        )

        conn.commit()

        return {
            "status": "success",
            "message": "Usuário inserido com sucesso"
        }

    except mysql.connector.Error as err: # Captura erro específico do MySQL
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro no banco de dados: {err.msg}"
        )
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )

    finally:
        # Só tenta fechar se eles foram criados, evitando erro caso a conexão falhe de início
        if cursor:
            cursor.close()
        if conn:
            conn.close()