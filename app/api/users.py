from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_current_supervisor, get_password_hash, get_current_user

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar agente",
    description="RF04 - Supervisor cria um novo agente.",
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor),
):
    if payload.role != UserRole.AGENTE:
        raise HTTPException(422, "Esta rota cria agentes. Use o comando administrativo para criar supervisores.")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username já existe")
    if payload.email and db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email já existe")

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.AGENTE,
        municipio=payload.municipio or current_user.municipio,
        supervisor_id=current_user.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="Listar agentes",
    description="Supervisor lista agentes sob sua responsabilidade.",
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    query = db.query(User).filter(User.role == UserRole.AGENTE)
    if current_user.role == UserRole.SUPERVISOR:
        query = query.filter(
            (User.supervisor_id == current_user.id)
        )
    return query.offset(skip).limit(limit).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obter usuário",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.id != current_user.id and user.supervisor_id != current_user.id:
        raise HTTPException(403, "Acesso negado")
    # Agente só vê a si mesmo; supervisor vê seus agentes
    if current_user.role == UserRole.AGENTE and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Editar usuário",
    description="RF04 - Supervisor edita ou desativa agente.",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.role != UserRole.AGENTE or user.supervisor_id != current_user.id:
        raise HTTPException(403, "Você só pode editar agentes da sua equipe")
    data = payload.model_dump(exclude_unset=True)
    if "supervisor_id" in data and data["supervisor_id"] != current_user.id:
        raise HTTPException(422, "Não é possível transferir agentes por esta rota")
    if "password" in data and data["password"]:
        data["hashed_password"] = get_password_hash(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    summary="Desativar usuário",
    description="RF04 - Soft-delete (desativa) o agente.",
)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if user.role != UserRole.AGENTE or user.supervisor_id != current_user.id:
        raise HTTPException(403, "Você só pode desativar agentes da sua equipe")
    user.is_active = False
    db.add(user)
    db.commit()
    return {"message": "Usuário desativado"}
