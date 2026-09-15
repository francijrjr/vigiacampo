from app.core.datas import agora_utc
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.registro import (
    RegistroDiario, Quarteirao, Imovel, Inspecao, Coleta,
    Especime, Tratamento, DepositoEliminado, StatusRegistro
)
from app.schemas.registro import (
    RegistroDiarioCreate, RegistroDiarioUpdate, RegistroDiarioResponse,
    RegistroDiarioListItem, SyncPayload, SyncResponse, SyncResultItem,
    QuarteiraoCreate, QuarteiraoResponse, ImovelCreate, ImovelResponse, ImovelUpdate,
)
from app.core.security import get_current_user, get_current_supervisor
from app.services.resumo import recalcular_resumos
from app.services.permissoes import pode_acessar, exigir_edicao

router = APIRouter(prefix="/registros", tags=["Registros Diários"])


def _can_access_registro(user: User, registro: RegistroDiario) -> bool:
    return pode_acessar(user, registro)


def _create_imovel_from_schema(db: Session, registro_id: int, im: ImovelCreate, quarteirao_map: dict = None) -> Imovel:
    if im.quarteirao_client_id:
        quarteirao = db.query(Quarteirao).filter_by(client_id=im.quarteirao_client_id, registro_id=registro_id).first()
        if not quarteirao:
            raise HTTPException(422, "Quarteirão offline não encontrado neste registro")
        if im.quarteirao_id and im.quarteirao_id != quarteirao.id:
            raise HTTPException(422, "Os identificadores do quarteirão não correspondem")
        im.quarteirao_id = quarteirao.id
    if im.quarteirao_id and not db.query(Quarteirao).filter_by(id=im.quarteirao_id, registro_id=registro_id).first():
        raise HTTPException(422, "O quarteirão deve pertencer ao mesmo registro")
    imovel = Imovel(
        client_id=im.client_id,
        registro_id=registro_id,
        quarteirao_id=im.quarteirao_id,
        numero=im.numero,
        complemento=im.complemento,
        logradouro=im.logradouro,
        lado=im.lado,
        tipo=im.tipo,
        hora_entrada=im.hora_entrada,
        tipo_visita=im.tipo_visita,
        pendencia=im.pendencia,
    )
    db.add(imovel)
    db.flush()

    for insp in im.inspecoes:
        total = insp.a1 + insp.a2 + insp.b + insp.c + insp.d1 + insp.d2 + insp.e
        db.add(Inspecao(
            client_id=insp.client_id,
            imovel_id=imovel.id,
            a1=insp.a1, a2=insp.a2, b=insp.b, c=insp.c,
            d1=insp.d1, d2=insp.d2, e=insp.e, total=total,
        ))
    for col in im.coletas:
        qtd = max(0, col.tubito_final - col.tubito_inicial + 1)
        db.add(Coleta(
            client_id=col.client_id,
            imovel_id=imovel.id,
            numero_amostra=col.numero_amostra,
            tubito_inicial=col.tubito_inicial,
            tubito_final=col.tubito_final,
            quantidade_tubitos=qtd,
        ))
    for esp in im.especimes:
        db.add(Especime(
            client_id=esp.client_id,
            imovel_id=imovel.id,
            especie=esp.especie,
            larvas=esp.larvas, pupas=esp.pupas,
            pupa_aedes=esp.pupa_aedes, adultos=esp.adultos,
        ))
    for trat in im.tratamentos:
        db.add(Tratamento(
            client_id=trat.client_id,
            imovel_id=imovel.id,
            categoria=trat.categoria,
            produto=trat.produto,
            quantidade=trat.quantidade,
            depositos_tratados=trat.depositos_tratados,
            cargas=trat.cargas,
        ))
    for dep in im.depositos_eliminados:
        db.add(DepositoEliminado(
            client_id=dep.client_id,
            imovel_id=imovel.id,
            tipo=dep.tipo,
            quantidade=dep.quantidade,
        ))
    return imovel


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

    registro = RegistroDiario(
        client_id=payload.client_id,
        agente_id=current_user.id,
        municipio=payload.municipio,
        codigo_area=payload.codigo_area,
        ciclo=payload.ciclo,
        data=payload.data,
        zona=payload.zona,
        atividade=payload.atividade,
        concluido=payload.concluido,
        observacoes=payload.observacoes,
        status=StatusRegistro.DRAFT,
    )
    db.add(registro)
    db.flush()

    for q in payload.quarteiroes:
        db.add(Quarteirao(
            client_id=q.client_id,
            registro_id=registro.id,
            numero=q.numero,
            sequencia=q.sequencia,
            lado=q.lado,
            logradouro=q.logradouro,
        ))
    db.flush()

    for im in payload.imoveis:
        _create_imovel_from_schema(db, registro.id, im)

    db.flush()
    recalcular_resumos(db, registro)
    db.commit()

    return (
        db.query(RegistroDiario)
        .options(
            joinedload(RegistroDiario.quarteiroes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.inspecoes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.coletas),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.especimes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.tratamentos),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.depositos_eliminados),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.fotos),
        )
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
        db.query(RegistroDiario)
        .options(
            joinedload(RegistroDiario.quarteiroes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.inspecoes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.coletas),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.especimes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.tratamentos),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.depositos_eliminados),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.fotos),
        )
        .filter(RegistroDiario.id == registro_id)
        .first()
    )
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if not _can_access_registro(current_user, registro):
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
    if not _can_access_registro(current_user, registro):
        raise HTTPException(status_code=403, detail="Acesso negado")
    exigir_edicao(current_user, registro)

    data = payload.model_dump(exclude_unset=True)
    if data.get("status") == StatusRegistro.SYNCED:
        data["synced_at"] = agora_utc()
        data["concluido"] = True
    for k, v in data.items():
        setattr(registro, k, v)
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
        db.query(RegistroDiario)
        .options(
            joinedload(RegistroDiario.quarteiroes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.inspecoes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.coletas),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.especimes),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.tratamentos),
            joinedload(RegistroDiario.imoveis).joinedload(Imovel.depositos_eliminados),
        )
        .filter(RegistroDiario.id == registro_id)
        .first()
    )
    if not original:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    if not _can_access_registro(current_user, original):
        raise HTTPException(status_code=403, detail="Acesso negado")

    novo = RegistroDiario(
        agente_id=current_user.id,
        municipio=original.municipio,
        codigo_area=original.codigo_area,
        ciclo=original.ciclo,
        data=date.today(),
        zona=original.zona,
        atividade=original.atividade,
        status=StatusRegistro.DRAFT,
        concluido=False,
        observacoes=original.observacoes,
    )
    db.add(novo)
    db.flush()

    q_map = {}
    for q in original.quarteiroes:
        nq = Quarteirao(
            registro_id=novo.id,
            numero=q.numero,
            sequencia=q.sequencia,
            lado=q.lado,
            logradouro=q.logradouro,
        )
        db.add(nq)
        db.flush()
        q_map[q.id] = nq.id
        if q.boletim:
            from app.models.boletim import BoletimReconhecimento
            cabecalho = {campo: getattr(q.boletim, campo) for campo in (
                'uf', 'distrito', 'municipio', 'localidade', 'subdistrito', 'sublocal', 'categoria', 'funcao_responsavel')}
            db.add(BoletimReconhecimento(quarteirao_id=nq.id, responsavel=current_user.full_name,
                                         data=novo.data, **cabecalho))

    for im in original.imoveis:
        imovel = Imovel(
            registro_id=novo.id,
            quarteirao_id=q_map.get(im.quarteirao_id) if im.quarteirao_id else None,
            numero=im.numero,
            complemento=im.complemento,
            logradouro=im.logradouro,
            lado=im.lado,
            tipo=im.tipo,
            hora_entrada=im.hora_entrada,
            tipo_visita=im.tipo_visita,
            pendencia=im.pendencia,
        )
        db.add(imovel)
        db.flush()
        for insp in im.inspecoes:
            db.add(Inspecao(
                imovel_id=imovel.id, a1=insp.a1, a2=insp.a2, b=insp.b, c=insp.c,
                d1=insp.d1, d2=insp.d2, e=insp.e, total=insp.total,
            ))
        for col in im.coletas:
            db.add(Coleta(
                imovel_id=imovel.id, numero_amostra=col.numero_amostra,
                tubito_inicial=col.tubito_inicial, tubito_final=col.tubito_final,
                quantidade_tubitos=col.quantidade_tubitos,
            ))
        for esp in im.especimes:
            db.add(Especime(
                imovel_id=imovel.id, especie=esp.especie,
                larvas=esp.larvas, pupas=esp.pupas, pupa_aedes=esp.pupa_aedes, adultos=esp.adultos,
            ))
        for trat in im.tratamentos:
            db.add(Tratamento(
                imovel_id=imovel.id, categoria=trat.categoria, produto=trat.produto,
                quantidade=trat.quantidade, depositos_tratados=trat.depositos_tratados, cargas=trat.cargas,
            ))
        for dep in im.depositos_eliminados:
            db.add(DepositoEliminado(imovel_id=imovel.id, tipo=dep.tipo, quantidade=dep.quantidade))

    db.flush()
    recalcular_resumos(db, novo)
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

        registro = RegistroDiario(
            client_id=reg_data.client_id,
            agente_id=current_user.id,
            municipio=reg_data.municipio,
            codigo_area=reg_data.codigo_area,
            ciclo=reg_data.ciclo,
            data=reg_data.data,
            zona=reg_data.zona,
            atividade=reg_data.atividade,
            concluido=True,
            observacoes=reg_data.observacoes,
            status=StatusRegistro.SYNCED,
            synced_at=agora_utc(),
        )
        db.add(registro)
        db.flush()

        for q in reg_data.quarteiroes:
            db.add(Quarteirao(
                client_id=q.client_id,
                registro_id=registro.id,
                numero=q.numero,
                sequencia=q.sequencia,
                lado=q.lado,
                logradouro=q.logradouro,
            ))
        db.flush()

        for im in reg_data.imoveis:
            _create_imovel_from_schema(db, registro.id, im)

        recalcular_resumos(db, registro)
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
    if not registro or not _can_access_registro(current_user, registro):
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
    if not registro or not _can_access_registro(current_user, registro):
        raise HTTPException(status_code=404, detail="Registro não encontrado ou acesso negado")
    exigir_edicao(current_user, registro)
    imovel = _create_imovel_from_schema(db, registro_id, payload)
    db.flush()
    recalcular_resumos(db, registro)
    db.commit()
    return (
        db.query(Imovel)
        .options(
            joinedload(Imovel.inspecoes),
            joinedload(Imovel.coletas),
            joinedload(Imovel.especimes),
            joinedload(Imovel.tratamentos),
            joinedload(Imovel.depositos_eliminados),
            joinedload(Imovel.fotos),
        )
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
    if not registro or not _can_access_registro(current_user, registro):
        raise HTTPException(status_code=404, detail="Registro não encontrado ou acesso negado")
    return (
        db.query(Imovel)
        .options(
            joinedload(Imovel.inspecoes),
            joinedload(Imovel.coletas),
            joinedload(Imovel.especimes),
            joinedload(Imovel.tratamentos),
            joinedload(Imovel.depositos_eliminados),
            joinedload(Imovel.fotos),
        )
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
    if not registro or not _can_access_registro(current_user, registro):
        raise HTTPException(status_code=404, detail="Registro não encontrado ou acesso negado")
    exigir_edicao(current_user, registro)
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id, Imovel.registro_id == registro_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    data = payload.model_dump(exclude_unset=True)
    if data.get("quarteirao_id") and not db.query(Quarteirao).filter_by(id=data["quarteirao_id"], registro_id=registro_id).first():
        raise HTTPException(422, "Quarteirão de outro registro")
    for k, v in data.items():
        setattr(imovel, k, v)
    db.add(imovel)
    db.flush()
    recalcular_resumos(db, registro)
    db.commit()
    return (
        db.query(Imovel)
        .options(
            joinedload(Imovel.inspecoes),
            joinedload(Imovel.coletas),
            joinedload(Imovel.especimes),
            joinedload(Imovel.tratamentos),
            joinedload(Imovel.depositos_eliminados),
            joinedload(Imovel.fotos),
        )
        .filter(Imovel.id == imovel.id)
        .first()
    )
