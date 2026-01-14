from pydantic import BaseModel, EmailStr
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