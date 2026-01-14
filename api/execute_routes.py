from fastapi import APIRouter, HTTPException
from api.connection import get_connection
from schemas.schemas import CriarConta, LoginSchema
import mysql.connector 

criar_router = APIRouter(prefix="/usuarios", tags=["usuarios"])
login_router = APIRouter(prefix="/loginUsuarios", tags=["login"])

@criar_router.post("")
async def insert_usuario(data: CriarConta):
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

    except mysql.connector.Error as err: 
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
        if cursor:
            cursor.close()
        if conn:
            conn.close()


DATA_API_URL = "http://127.0.0.1:8001"
INTERNAL_KEY = "INTERNAL_SECRET"


@login_router.post("")
async def login_usuario(data: LoginSchema):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, senha FROM usuarios WHERE email = %s",
            (data.email,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado"
            )

        return {
            "id": user["id"],
            "senha": user["senha"]
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()