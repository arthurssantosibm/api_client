from fastapi import APIRouter, Body, HTTPException, Depends, Header
from api.connection import get_connection
from schemas.schemas import CriarConta, LoginSchema, UpdateUserSchema, TransacaoDataPayload, DepositoDBRequest, DepositoDBResponse, ReativarSchema, SaqueDBRequest, SaqueDBResponse, TransactionCreateSchema
from api.jwt import create_access_token, get_current_user_id
import mysql.connector
from jose import jwt, JWTError

criar_router = APIRouter(prefix="/usuarios", tags=["usuarios"])
login_router = APIRouter(prefix="/loginUsuarios", tags=["login"])
update_router = APIRouter(prefix="/updateUsuarios", tags=["update"])
transacoes_router = APIRouter(prefix="/transacoesUsuarios", tags=["transacoes"])
deposit_router = APIRouter(prefix="/deposito", tags=["deposito"])
saque_router = APIRouter(prefix="/saque", tags=["saque"])
invest_router = APIRouter(prefix="/invest", tags=["invest"])

DATA_API_URL = "http://127.0.0.1:8001"
API_CORE_VALIDATE_URL = "http://127.0.0.1:8000/transacoes/transacoes/"
INTERNAL_KEY = "INTERNAL_SECRET"


# BLOCO DE CRIAR CONTA
@criar_router.post("")
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

# BLOCO DE LOGIN
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
            
# BLOCO DE UPDATE USUÁRIO         
@update_router.put("/{user_id}")
async def update_usuario(user_id: int, data: UpdateUserSchema):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id FROM usuarios WHERE id = %s",
            (user_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado"
            )

        fields = []
        values = []

        if data.nome is not None:
            fields.append("nome=%s")
            values.append(data.nome)

        if data.email is not None:
            fields.append("email=%s")
            values.append(data.email)

        if data.telefone is not None:
            fields.append("telefone=%s")
            values.append(data.telefone)

        if data.senha is not None:
            fields.append("senha=%s")
            values.append(data.senha)

        if not fields:
            raise HTTPException(
                status_code=400,
                detail="Nenhum dado para atualizar"
            )

        query = f"""
            UPDATE usuarios
            SET {", ".join(fields)}
            WHERE id=%s
        """

        values.append(user_id)
        cursor.execute(query, tuple(values))
        conn.commit()

        return {"message": "Dados atualizados com sucesso"}

    finally:
        cursor.close()
        conn.close()

# BLOCO DE SUSPENDER CONTA
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

# BLOCO DE REATIVAR CONTA POR E-MAIL
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

# BLOCO DE REALIZAR DEPÓSITO
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
            raise HTTPException(status_code=400, detail="Valor inválido")


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
        
# BLOCO DE EXECUTAR TRANSAÇÃO
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
        
# BLOCO DE REALIZAR SAQUE
@saque_router.post(
    "",
    response_model=SaqueDBResponse
)
async def realizar_saque(
    data: SaqueDBRequest,
    x_internal_key: str = Header(..., alias="X-Internal-Key")
):

    if x_internal_key != INTERNAL_KEY:
        raise HTTPException(status_code=403, detail="Acesso negado")

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor(dictionary=True)

    try:
        if data.valor <= 0:
            raise HTTPException(status_code=400, detail="Valor inválido")


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
        if data.valor > user["saldo_cc"]:
            raise HTTPException(status_code=400, detail="Saldo insuficiente")


        cursor.execute(
            """
            UPDATE usuarios
            SET saldo_cc = saldo_cc - %s
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
                data.email,
                "SAQUE",
                data.valor,
                "Saque efetuado"
            )
        )

        cursor.execute(
            "SELECT saldo_cc FROM usuarios WHERE email = %s",
            (data.email,)
        )
        saldo_atual = cursor.fetchone()["saldo_cc"]

        conn.commit()

        return SaqueDBResponse(
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

@invest_router.post("/create", status_code=201)
async def criar_transacao(data: TransactionCreateSchema):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO financial_transactions (
                client_id, email, valor_investido,
                nome_ativo, valor_atual,
                rentabilidade, tipo_ativo
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            data.client_id,
            data.email,
            data.valor_investido,
            data.nome_ativo,
            data.valor_atual,
            data.rentabilidade,
            data.tipo_ativo
        ))

        # 2️⃣ Atualizar patrimônio total
        cursor.execute("""
            UPDATE invest_client
            SET patrimonio_total = patrimonio_total + %s
            WHERE client_id = %s
        """, (
            data.valor_atual,
            data.client_id
        ))

        conn.commit()

        return {"message": "Transação registrada"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))