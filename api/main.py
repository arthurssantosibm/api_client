from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from fastapi import FastAPI
from api.execute_routes import criar_router
from api.execute_routes import login_router
from api.execute_routes import update_router
from api.execute_routes import transacoes_router
from api.execute_routes import deposit_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(criar_router)
app.include_router(login_router)
app.include_router(update_router)
app.include_router(transacoes_router)
app.include_router(deposit_router)
