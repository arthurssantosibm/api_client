from pydantic import BaseModel, EmailStr, Field, PositiveFloat
from datetime import datetime
from typing import Optional

class CriarConta(BaseModel):
    nome: str
    email: EmailStr
    telefone: str
    senha: str
    
class LoginSchema(BaseModel, extra="ignore"):
    email: EmailStr
    senha: str
        

class ReativarSchema(BaseModel):
    email: EmailStr
    

        
class UpdateUserSchema(BaseModel):
    nome: str
    email: EmailStr
    telefone: str
    current_password: Optional[str] = None
    senha: Optional[str] = None
    

class TransacaoDataPayload(BaseModel):
    email_origin: EmailStr
    user_origin_id: int
    email_destination: EmailStr
    valor: float
    mensagem: Optional[str] = None
    
class DepositoDBRequest(BaseModel):
    email: EmailStr
    valor: float
    
class DepositoDBResponse(BaseModel):
    saldo_atual: float
    
class SaqueDBRequest(BaseModel):
    email: EmailStr
    valor: float
    
class SaqueDBResponse(BaseModel):
    saldo_atual: float


class TransactionCreateSchema(BaseModel):
    client_id: int = Field(
        ...,
        description="ID do usuário (FK usuarios.id)"
    )

    email: str = Field(
        ...,
        max_length=255,
        description="Email do cliente que realizou a compra"
    )

    nome_ativo: str = Field(
        ...,
        max_length=150,
        description="Nome do ativo adquirido"
    )

    tipo_ativo: str = Field(
        ...,
        max_length=50,
        description="Tipo do ativo (cripto, renda fixa, fundo, ações)"
    )

    quantidade: PositiveFloat = Field(
        ...,
        description="Quantidade de cotas/unidades compradas"
    )

    preco_unitario: PositiveFloat = Field(
        ...,
        description="Preço unitário do ativo no momento da compra"
    )

    valor_investido: PositiveFloat = Field(
        ...,
        description="Valor total pago (preco_unitario * quantidade)"
    )

    valor_atual: PositiveFloat = Field(
        ...,
        description="Valor atual do ativo no momento da compra"
    )

    rentabilidade: Optional[float] = Field(
        default=0,
        description="Rentabilidade inicial (0 no momento da compra)"
    )