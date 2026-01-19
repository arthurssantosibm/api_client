import pytest
from fastapi import HTTPException
from jose import JWTError
from unittest.mock import patch


# ============================
# create_access_token
# ============================

def test_create_access_token_sucesso():
    with patch("api.jwt.SECRET_KEY", "chave_teste"):
        from api.jwt import create_access_token

        token = create_access_token({"sub": "1"})

        assert isinstance(token, str)
        assert token


def test_create_access_token_sem_secret_key():
    with patch("api.jwt.SECRET_KEY", None):
        from api.jwt import create_access_token

        with pytest.raises(RuntimeError) as exc:
            create_access_token({"sub": "1"})

        assert "SECRET_KEY não carregada" in str(exc.value)


# ============================
# get_current_user_id
# ============================

def test_get_current_user_id_sucesso():
    with patch("api.jwt.SECRET_KEY", "chave_teste"):
        from api.jwt import create_access_token, get_current_user_id

        token = create_access_token({"sub": "42"})
        user_id = get_current_user_id(token)

        assert user_id == 42


def test_get_current_user_id_sem_sub():
    with patch("api.jwt.SECRET_KEY", "chave_teste"):
        from api.jwt import create_access_token, get_current_user_id

        token = create_access_token({})

        with pytest.raises(HTTPException) as exc:
            get_current_user_id(token)

        assert exc.value.status_code == 401
        assert exc.value.detail == "Token inválido"


def test_get_current_user_id_jwt_error():
    with patch("api.jwt.SECRET_KEY", "chave_teste"):
        from api.jwt import get_current_user_id

        with pytest.raises(HTTPException) as exc:
            get_current_user_id("token_invalido_total")

        assert exc.value.status_code == 401
        assert exc.value.detail == "Token inválido"
