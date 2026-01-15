from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class CriarConta(BaseModel):
    nome: str
    email: EmailStr
    telefone: str
    senha: str
    
class LoginSchema(BaseModel):
    email: EmailStr
    
    class Config:
        from_attributes = True
        
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
    valor: float = Field(..., gt=0)
    
class DepositoDBResponse(BaseModel):
    saldo_atual: float
