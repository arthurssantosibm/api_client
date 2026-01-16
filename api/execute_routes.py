from fastapi import APIRouter, Body, HTTPException, Depends, Header
from api.connection import get_connection
from schemas.schemas import CriarConta, LoginSchema, UpdateUserSchema, TransacaoDataPayload, DepositoDBRequest, DepositoDBResponse, ReativarSchema
from api.jwt import create_access_token, get_current_user_id
import mysql.connector 
import requests

criar_router = APIRouter(prefix="/usuarios", tags=["usuarios"])
login_router = APIRouter(prefix="/loginUsuarios", tags=["login"])
update_router = APIRouter(prefix="/updateUsuarios", tags=["update"])
transacoes_router = APIRouter(prefix="/transacoesUsuarios", tags=["transacoes"])
deposit_router = APIRouter(prefix="/deposito", tags=["deposito"])

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
API_CORE_VALIDATE_URL = "http://127.0.0.1:8000/transacoes/transacoes/"
INTERNAL_KEY = "INTERNAL_SECRET"



@login_router.post("")
async def login_usuario(
    data: LoginSchema,
    x_internal_key: str = Header(..., alias="X-Internal-Key")
):

    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT id, senha, correntista FROM usuarios WHERE email = %s",
        (data.email,)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user["correntista"] == 0:
        raise HTTPException(status_code=403, detail="CONTA_INATIVA")

    return {"id": user["id"], "senha": user["senha"]}

            
            
@update_router.put("/{user_id}")
async def update_usuario(user_id: int, data: UpdateUserSchema):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        if data.senha:
            cursor.execute(
                """
                UPDATE usuarios
                SET nome=%s, email=%s, telefone=%s, senha=%s
                WHERE id=%s
                """,
                (data.nome, data.email, data.telefone, data.senha, user_id)
            )
        else:
            cursor.execute(
                """
                UPDATE usuarios
                SET nome=%s, email=%s, telefone=%s
                WHERE id=%s
                """,
                (data.nome, data.email, data.telefone, user_id)
            )

        conn.commit()
        return {"message": "Dados atualizados com sucesso"}
    finally:
        cursor.close()
        conn.close()


@update_router.put("/suspender/{user_id}")
async def suspender_conta(
    user_id: int, 
    x_internal_key: str = Header(..., alias="X-Internal-Key")
):
    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE usuarios SET correntista = 0 WHERE id = %s", (user_id,))
        conn.commit()
        return {"message": "Conta suspensa com sucesso"}
    finally:
        cursor.close()
        conn.close()



@update_router.put("/reativar_por_email/")
async def reativar_conta_por_email(
    data: ReativarSchema = Body(...),
    x_internal_key: str = Header(..., alias="X-Internal-Key")
):
    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")

    email = data.email.strip().lower()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE usuarios SET correntista = 1 WHERE LOWER(email) = %s",
            (email,)
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="E-mail não encontrado"
            )

        return {"message": "Conta reativada com sucesso"}

    finally:
        cursor.close()
        conn.close()





@transacoes_router.post("")
async def executar_transacao_data(
    payload: TransacaoDataPayload,
    x_internal_key: str = Header(..., alias="X-Internal-Key")
):
    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    try:
        # 🔹 Registro da transação
        cursor.execute(
            """
            INSERT INTO transacoes
                (email_origin, email_destination, valor, mensagem, create_time)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (
                payload.email_origin,
                payload.email_destination,
                payload.valor,
                payload.mensagem
            )
        )

        # 🔹 Debita usuário origem
        cursor.execute(
            "UPDATE usuarios SET saldo_cc = saldo_cc - %s WHERE id = %s",
            (payload.valor, payload.user_origin_id)
        )

        # 🔹 Credita usuário destino
        cursor.execute(
            "UPDATE usuarios SET saldo_cc = saldo_cc + %s WHERE email = %s",
            (payload.valor, payload.email_destination)
        )

        conn.commit()
        return {"status": "ok"}

    except mysql.connector.Error as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro no banco: {str(e)}"
        )

    finally:
        cursor.close()
        conn.close()
        
        
@deposit_router.post(
    "",
    response_model=DepositoDBResponse
)
async def realizar_deposito(
    data: DepositoDBRequest,
    x_internal_key: str = Header(..., alias="X-Internal-Key")
):

    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    try:
        if data.valor <= 0:
            raise HTTPException(
                status_code=400,
                detail="Valor inválido"
            )

        cursor.execute(
            "SELECT id, saldo_cc FROM usuarios WHERE email = %s",
            (data.email,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado"
            )

        cursor.execute(
            """
            UPDATE usuarios
            SET saldo_cc = saldo_cc + %s
            WHERE email = %s
            """,
            (data.valor, data.email)
        )

        cursor.execute(
            """
            INSERT INTO transacoes
                (email_origin, email_destination, valor, mensagem, create_time)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (
                "DEPOSITO",
                data.email,
                data.valor,
                "Depósito em conta"
            )
        )

        cursor.execute(
            "SELECT saldo_cc FROM usuarios WHERE email = %s",
            (data.email,)
        )
        saldo_atual = cursor.fetchone()["saldo_cc"]

        conn.commit()

        return DepositoDBResponse(
            saldo_atual=saldo_atual
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro no banco de dados: {err.msg}"
        )

    finally:
        cursor.close()
        conn.close()

