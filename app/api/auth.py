from app.core.datas import agora_utc
from datetime import timedelta, datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    LoginRequest, Token, UserResponse, ChangePasswordRequest, TokenRefresh
)
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token, get_current_user
)
from app.core.config import settings
from app.core.security import assinatura_senha, validar_sessao, oauth2_scheme
from app.models.sessao import SessaoRevogada

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login de usuário",
    description="RF01 - Autentica Agente ou Supervisor e retorna token JWT.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")

    sessao = {"sid": uuid4().hex, "senha": assinatura_senha(user)}
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "username": user.username, **sessao},
    )
    refresh_token = create_refresh_token(subject=user.id, extra_claims=sessao)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renovar token",
    description="Renova o access token a partir de um refresh token válido.",
)
def refresh_token(payload: TokenRefresh, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")
    user_id = data.get("sub")
    if not str(user_id).isdigit():
        raise HTTPException(401, "Sessão inválida")
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    validar_sessao(data, user, db)

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "username": user.username, "sid": data["sid"], "senha": data["senha"]},
    )
    return Token(
        access_token=access_token,
        refresh_token=payload.refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    summary="Logout",
    description="Encerra a sessão no servidor, incluindo a renovação de acesso.",
)
def logout(current_user: User = Depends(get_current_user), token=Depends(oauth2_scheme), db: Session = Depends(get_db)):
    dados = decode_token(token.credentials)
    db.merge(SessaoRevogada(id=dados["sid"], expira_em=agora_utc()+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)))
    db.commit()
    return {"message": "Sessão encerrada"}


@router.post(
    "/change-password",
    summary="Alterar senha",
    description="RF02 - Altera a senha do usuário autenticado.",
)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual incorreta")
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(current_user)
    db.commit()
    return {"message": "Senha alterada com sucesso"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Usuário atual",
    description="Retorna os dados do usuário autenticado.",
)
def me(current_user: User = Depends(get_current_user)):
    return current_user
