from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from io import BytesIO
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.registro import RegistroDiario, Imovel, Inspecao, StatusRegistro
from app.schemas.registro import StatsAgente, RegistroDiarioResponse
from app.core.security import get_current_supervisor, get_current_user
from app.services.resumo import recalcular_resumos
from app.services.permissoes import pode_acessar

router = APIRouter(prefix="/relatorios", tags=["Relatórios e Estatísticas"])


@router.get(
    "/estatisticas",
    response_model=List[StatsAgente],
    summary="Estatísticas agregadas",
    description="RF26 - Supervisor consulta estatísticas por agente, zona ou período.",
)
def estatisticas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    zona: Optional[str] = Query(None),
):
    query = (
        db.query(
            RegistroDiario.agente_id,
            User.full_name,
            func.count(RegistroDiario.id).label("total_registros"),
            func.coalesce(func.sum(RegistroDiario.resumo_imoveis_trabalhados), 0).label("total_imoveis"),
            func.coalesce(func.sum(RegistroDiario.resumo_depositos_inspecionados), 0).label("total_inspecoes"),
            func.min(RegistroDiario.data).label("periodo_inicio"),
            func.max(RegistroDiario.data).label("periodo_fim"),
        )
        .join(User, User.id == RegistroDiario.agente_id)
        .filter(RegistroDiario.status == StatusRegistro.SYNCED)
        .filter((User.supervisor_id == current_user.id) | (User.id == current_user.id))
    )
    if data_inicio:
        query = query.filter(RegistroDiario.data >= data_inicio)
    if data_fim:
        query = query.filter(RegistroDiario.data <= data_fim)
    if zona:
        query = query.filter(RegistroDiario.zona == zona)

    rows = query.group_by(RegistroDiario.agente_id, User.full_name).all()
    return [
        StatsAgente(
            agente_id=r.agente_id,
            agente_nome=r.full_name,
            total_registros=r.total_registros,
            total_imoveis=int(r.total_imoveis or 0),
            total_inspecoes=int(r.total_inspecoes or 0),
            periodo_inicio=r.periodo_inicio,
            periodo_fim=r.periodo_fim,
        )
        for r in rows
    ]


@router.get(
    "/registro/{registro_id}/resumo",
    summary="Resumo calculado do verso da ficha",
    description="RF24 - Retorna os totais automáticos do registro.",
)
def resumo_ficha(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registro = db.query(RegistroDiario).filter(RegistroDiario.id == registro_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if not pode_acessar(current_user, registro):
        raise HTTPException(403, "Acesso negado")
    recalcular_resumos(db, registro)
    return {
        "registro_id": registro.id,
        "imoveis_trabalhados": registro.resumo_imoveis_trabalhados,
        "pendencias": registro.resumo_pendencias,
        "depositos_inspecionados": registro.resumo_depositos_inspecionados,
        "imoveis_com_especimes": registro.resumo_imoveis_com_especimes,
        "totais_tratamento": registro.resumo_totais_tratamento,
        "exemplares_encontrados": registro.resumo_exemplares,
    }


@router.get(
    "/registro/{registro_id}/pdf",
    summary="Exportar PDF da ficha",
    description="RF25/RF27 - Gera PDF simplificado da ficha (layout oficial pode ser customizado).",
    responses={200: {"description": "PDF do registro, sem fotos", "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}}},
)
def export_pdf(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_supervisor),
):
    registro = (
        db.query(RegistroDiario)
        .filter(RegistroDiario.id == registro_id)
        .first()
    )
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    if not pode_acessar(current_user, registro):
        raise HTTPException(403, "Acesso negado")
    recalcular_resumos(db, registro)

    from app.services.pdf import gerar_pdf
    content = gerar_pdf(registro)

    return StreamingResponse(
        BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="ficha_{registro_id}.pdf"'},
    )
