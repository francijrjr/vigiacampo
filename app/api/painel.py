from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.registro import RegistroDiario, StatusRegistro

router = APIRouter(tags=["Painel"])


class ResumoPainel(BaseModel):
    total_registros: int
    total_imoveis: int
    total_enviados: int
    total_rascunhos: int


@router.get("/painel", response_model=ResumoPainel, summary="Consultar totais do painel")
def painel(db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    consulta = db.query(RegistroDiario).join(User, RegistroDiario.agente_id == User.id)
    if usuario.role == UserRole.SUPERVISOR:
        consulta = consulta.filter((User.id == usuario.id) | (User.supervisor_id == usuario.id))
    else:
        consulta = consulta.filter(User.id == usuario.id)
    return ResumoPainel(total_registros=consulta.count(),
        total_imoveis=consulta.with_entities(func.coalesce(func.sum(RegistroDiario.resumo_imoveis_trabalhados), 0)).scalar(),
        total_enviados=consulta.filter(RegistroDiario.status == StatusRegistro.SYNCED).count(),
        total_rascunhos=consulta.filter(RegistroDiario.status != StatusRegistro.SYNCED).count())
