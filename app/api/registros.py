"""Rotas HTTP de registros; persistência e cópia ficam nos serviços."""
from datetime import date
from typing import List, Optional

from app.core.datas import agora_utc
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.registro import (
    RegistroDiario, Quarteirao, Imovel, StatusRegistro
)
from app.schemas.registro import (
    RegistroDiarioCreate, RegistroDiarioUpdate, RegistroDiarioResponse,
    RegistroDiarioListItem, SyncPayload, SyncResponse, SyncResultItem,
    QuarteiraoCreate, QuarteiraoResponse, ImovelCreate, ImovelResponse, ImovelUpdate,
)
from app.core.security import get_current_user
from app.services.resumo import recalcular_resumos
from app.services.permissoes import pode_acessar, exigir_edicao

from app.services.registros import (
    criar_imovel, criar_registro, copiar_registro,
    consultar_registros_completos, consultar_imoveis_completos,
)

router = APIRouter(prefix="/registros", tags=["Registros Diários"])


@router.post(
    "/",
    response_model=RegistroDiarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Registro Diário",
    description="RF06 - Cria um novo registro diário com dados básicos e opcionalmente quarteirões/imóveis.",
)
def create_registro(
    payload: RegistroDiarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.client_id:
        existing = db.query(RegistroDiario).filter(RegistroDiario.client_id == payload.client_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Registro com este client_id já existe (idempotência)")

    registro = criar_registro(db, payload, current_user.id)
    db.commit()

    return (
        consultar_registros_completos(db)
        .filter(RegistroDiario.id == registro.id)
        .first()
    )


@router.get(
    "/",
    response_model=List[RegistroDiarioListItem],
    summary="Listar registros",
    description="RF08 - Histórico de registros do agente (ou de todos para supervisor), com filtros.",
)
def list_registros(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    zona: Optional[str] = Query(None),
    status: Optional[StatusRegistro] = Query(None),
    agente_id: Optional[int] = Query(None, description="Apenas supervisor"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = db.query(RegistroDiario)
    if current_user.role == UserRole.SUPERVISOR:
        query = query.join(User, RegistroDiario.agente_id == User.id).filter((User.supervisor_id == current_user.id) | (User.id == current_user.id))
    if current_user.role == UserRole.AGENTE:
        query = query.filter(RegistroDiario.agente_id == current_user.id)
    elif agente_id:
        query = query.filter(RegistroDiario.agente_id == agente_id)

    if data_inicio:
        query = query.filter(RegistroDiario.data >= data_inicio)
    if data_fim:
        query = query.filter(RegistroDiario.data <= data_fim)
    if zona:
        query = query.filter(RegistroDiario.zona == zona)
    if status:
        query = query.filter(RegistroDiario.status == status)

    return query.order_by(RegistroDiario.data.desc(), RegistroDiario.id.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{registro_id}",
    response_model=RegistroDiarioResponse,
    summary="Obter registro completo",
)
def get_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registro = (
        consultar_registros_completos(db)
        .filter(RegistroDiario.id == registro_id)
        .first()
    )
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if not pode_acessar(current_user, registro):
        raise HTTPException(status_code=403, detail="Acesso negado")
    return registro


@router.patch(
    "/{registro_id}",
    response_model=RegistroDiarioResponse,
    summary="Editar registro",
    description="RF07 - Edita registro pertencente ao agente ou sob supervisão.",
)
def update_registro(
    registro_id: int,
    payload: RegistroDiarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registro = db.query(RegistroDiario).filter(RegistroDiario.id == registro_id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if not pode_acessar(current_user, registro):
        raise HTTPException(status_code=403, detail="Acesso negado")
    exigir_edicao(current_user, registro)

    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == StatusRegistro.SYNCED:
        data["synced_at"] = agora_utc()
        data["concluido"] = True
    for campo, valor in data.items():
        setattr(registro, campo, valor)
    db.add(registro)
    db.flush()
    recalcular_resumos(db, registro)
    db.commit()
    return get_registro(registro_id, db, current_user)


@router.post(
    "/{registro_id}/duplicar",
    response_model=RegistroDiarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicar registro",
    description="RF09 - Cria uma cópia do registro (útil para dias semelhantes).",
)
def duplicar_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original = (
        consultar_registros_completos(db)
        .filter(RegistroDiario.id == registro_id)
        .first()
    )
    if not original:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if not pode_acessar(current_user, original):
        raise HTTPException(status_code=403, detail="Acesso negado")

    novo = copiar_registro(db, original, current_user)
    db.commit()
    return get_registro(novo.id, db, current_user)


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Sincronização em lote (offline)",
    description="RF11/RF12 - Recebe múltiplos registros criados offline. Idempotente via client_id.",
)
def sync_registros(
    payload: SyncPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = []
    created = 0
    skipped = 0

    for reg_data in payload.registros:
        if reg_data.client_id:
            existing = db.query(RegistroDiario).filter(RegistroDiario.client_id == reg_data.client_id).first()
            if existing:
                if existing.agente_id != current_user.id:
                    raise HTTPException(409, "Identificador já utilizado")
                results.append(SyncResultItem(
                    client_id=reg_data.client_id,
                    server_id=existing.id,
                    status="skipped",
                    message="Já sincronizado anteriormente",
                ))
                skipped += 1
                continue

        registro = criar_registro(db, reg_data, current_user.id, sincronizado=True)
        results.append(SyncResultItem(
            client_id=reg_data.client_id,
            server_id=registro.id,
            status="created",
        ))
        created += 1

    db.commit()
    return SyncResponse(
        results=results,
        total_processed=len(results),
        total_created=created,
        total_skipped=skipped,
    )


# ---------- Quarteirões e Imóveis aninhados ----------

@router.post(
    "/{registro_id}/quarteiroes",
    response_model=QuarteiraoResponse,
    status_code=201,
    summary="Cadastrar quarteirão",
    description="RF13",
)
def add_quarteirao(
    registro_id: int,
    payload: QuarteiraoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registro = db.query(RegistroDiario).filter(RegistroDiario.id == registro_id).first()
    if not registro or not pode_acessar(current_user, registro):
        raise HTTPException(status_code=404, detail="Registro não encontrado ou acesso negado")
    exigir_edicao(current_user, registro)
    q = Quarteirao(
        client_id=payload.client_id,
        registro_id=registro_id,
        numero=payload.numero,
        sequencia=payload.sequencia,
        lado=payload.lado,
        logradouro=payload.logradouro,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.post(
    "/{registro_id}/imoveis",
    response_model=ImovelResponse,
    status_code=201,
    summary="Cadastrar imóvel",
    description="RF14",
)
def add_imovel(
    registro_id: int,
    payload: ImovelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registro = db.query(RegistroDiario).filter(RegistroDiario.id == registro_id).first()
    if not registro or not pode_acessar(current_user, registro):
        raise HTTPException(status_code=404, detail="Registro não encontrado ou acesso negado")
    exigir_edicao(current_user, registro)
    imovel = criar_imovel(db, registro_id, payload)
    db.flush()
    recalcular_resumos(db, registro)
    db.commit()
    return (
        consultar_imoveis_completos(db)
        .filter(Imovel.id == imovel.id)
        .first()
    )


@router.get(
    "/{registro_id}/imoveis",
    response_model=List[ImovelResponse],
    summary="Listar imóveis do registro",
    description="RF15",
)
def list_imoveis(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registro = db.query(RegistroDiario).filter(RegistroDiario.id == registro_id).first()
    if not registro or not pode_acessar(current_user, registro):
        raise HTTPException(status_code=404, detail="Registro não encontrado ou acesso negado")
    return (
        consultar_imoveis_completos(db)
        .filter(Imovel.registro_id == registro_id)
        .all()
    )


@router.patch(
    "/{registro_id}/imoveis/{imovel_id}",
    response_model=ImovelResponse,
    summary="Editar imóvel",
    description="RF15",
)
def update_imovel(
    registro_id: int,
    imovel_id: int,
    payload: ImovelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registro = db.query(RegistroDiario).filter(RegistroDiario.id == registro_id).first()
    if not registro or not pode_acessar(current_user, registro):
        raise HTTPException(status_code=404, detail="Registro não encontrado ou acesso negado")
    exigir_edicao(current_user, registro)
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id, Imovel.registro_id == registro_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    data = payload.model_dump(exclude_unset=True)
    if data.get("quarteirao_id") and not db.query(Quarteirao).filter_by(id=data["quarteirao_id"], registro_id=registro_id).first():
        raise HTTPException(422, "Quarteirão de outro registro")
    for campo, valor in data.items():
        setattr(imovel, campo, valor)
    db.add(imovel)
    db.flush()
    recalcular_resumos(db, registro)
    db.commit()
    return (
        consultar_imoveis_completos(db)
        .filter(Imovel.id == imovel.id)
        .first()
    )
