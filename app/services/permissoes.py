"""Regras de acesso compartilhadas por todas as rotas."""
from fastapi import HTTPException
from app.models.user import UserRole
from app.models.registro import StatusRegistro


def pode_acessar(usuario, registro):
    return registro.agente_id == usuario.id or (
        usuario.role == UserRole.SUPERVISOR
        and registro.agente.supervisor_id == usuario.id
    )


def exigir_edicao(usuario, registro):
    if not pode_acessar(usuario, registro):
        raise HTTPException(403, "Você não tem acesso a este registro")
    if registro.status == StatusRegistro.SYNCED and usuario.role != UserRole.SUPERVISOR:
        raise HTTPException(409, "Registro enviado. Peça ao supervisor para corrigir os dados.")
