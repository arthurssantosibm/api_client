from fastapi import APIRouter, HTTPException
from api.connection import get_connection
from schemas.schemas import CriarConta

router = APIRouter()

insert_router = APIRouter(prefix="/db", tags=["db_querys"])

@router.post("/insert_usuarios")
async def insert_usuario(data: CriarConta):
    conn = get_connection()
    cursor = conn.cursor()

    try:
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
            "status": "ok",
            "message": "Usuário inserido com sucesso"
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erro ao inserir usuário"
        )

    finally:
        cursor.close()
        conn.close()