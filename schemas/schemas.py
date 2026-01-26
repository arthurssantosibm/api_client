from pydantic import BaseModel, EmailStr, Field, PositiveFloat
from decimal import Decimal
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
    client_id: int
    email: EmailStr

    ticker: str
    nome_ativo: str
    tipo_ativo: str

    quantidade: Decimal

    valor_investido: Decimal
    valor_atual: Decimal
    rentabilidade: Decimal
