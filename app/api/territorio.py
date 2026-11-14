"""Rotas HTTP para o módulo de Reconhecimento Geográfico."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.territorio import CadastroTerritorial
from app.models.user import User, UserRole
from app.schemas.territorio import (
    ResumoTerritorio,
    TerritorioCreate,
    TerritorioResponse,
)

router = APIRouter(prefix="/territorio", tags=["Reconhecimento Geográfico"])


def ids_equipe(db: Session, usuario: User) -> list[int]:
    if usuario.role == UserRole.SUPERVISOR:
        agentes = db.query(User.id).filter(User.supervisor_id == usuario.id).all()
        return [usuario.id, *[a[0] for a in agentes]]
    if usuario.supervisor_id:
        colegas = (
            db.query(User.id)
            .filter(
                (User.supervisor_id == usuario.supervisor_id)
                | (User.id == usuario.supervisor_id)
            )
            .all()
        )
        return list({usuario.id, *[c[0] for c in colegas]})
    return [usuario.id]


def consulta_escopo(db: Session, usuario: User):
    return db.query(CadastroTerritorial).filter(
        CadastroTerritorial.criado_por_id.in_(ids_equipe(db, usuario))
    )


@router.get(
    "/resumo",
    response_model=ResumoTerritorio,
    summary="Resumo do cadastro territorial",
)
def resumo_territorio(
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    base = consulta_escopo(db, usuario)
    itens = base.all()
    localidades = {
        (item.municipio.strip().lower(), item.localidade.strip().lower())
        for item in itens
    }
    mapeados = sum(1 for item in itens if item.geometria)
    total_imoveis = sum(item.total_imoveis for item in itens)
    return ResumoTerritorio(
        total_localidades=len(localidades),
        total_quarteiroes=len(itens),
        total_mapeados=mapeados,
        total_imoveis=total_imoveis,
    )


@router.get(
    "/",
    response_model=List[TerritorioResponse],
    summary="Listar quarteirões do cadastro territorial",
)
def listar_territorio(
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
    localidade: Optional[str] = Query(None),
    zona: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
):
    query = consulta_escopo(db, usuario)
    if localidade:
        query = query.filter(
            func.lower(CadastroTerritorial.localidade).contains(localidade.strip().lower())
        )
    if zona:
        query = query.filter(CadastroTerritorial.zona == zona.strip())
    if categoria:
        query = query.filter(CadastroTerritorial.categoria == categoria.strip())
    return query.order_by(
        CadastroTerritorial.localidade.asc(),
        CadastroTerritorial.quarteirao_numero.asc(),
        CadastroTerritorial.id.desc(),
    ).all()


@router.post(
    "/",
    response_model=TerritorioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar quarteirão no reconhecimento geográfico",
)
def criar_territorio(
    payload: TerritorioCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    existente = (
        consulta_escopo(db, usuario)
        .filter(
            func.lower(CadastroTerritorial.municipio) == payload.municipio.lower(),
            func.lower(CadastroTerritorial.localidade) == payload.localidade.lower(),
            CadastroTerritorial.quarteirao_numero == payload.quarteirao_numero,
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=409,
            detail="Já existe um quarteirão com este número nesta localidade.",
        )
    item = CadastroTerritorial(
        criado_por_id=usuario.id,
        **payload.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put(
    "/{territorio_id}",
    response_model=TerritorioResponse,
    summary="Atualizar quarteirão do cadastro territorial",
)
def atualizar_territorio(
    territorio_id: int,
    payload: TerritorioCreate,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    item = (
        consulta_escopo(db, usuario)
        .filter(CadastroTerritorial.id == territorio_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cadastro territorial não encontrado")
    duplicado = (
        consulta_escopo(db, usuario)
        .filter(
            CadastroTerritorial.id != territorio_id,
            func.lower(CadastroTerritorial.municipio) == payload.municipio.lower(),
            func.lower(CadastroTerritorial.localidade) == payload.localidade.lower(),
            CadastroTerritorial.quarteirao_numero == payload.quarteirao_numero,
        )
        .first()
    )
    if duplicado:
        raise HTTPException(
            status_code=409,
            detail="Já existe outro quarteirão com este número nesta localidade.",
        )
    dados = payload.model_dump(exclude_unset=True)
    if "geometria" not in dados:
        dados["geometria"] = item.geometria
    for campo, valor in dados.items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    "/{territorio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir quarteirão do cadastro territorial (restrito ao supervisor)",
)
def excluir_territorio(
    territorio_id: int,
    db: Session = Depends(get_db),
    usuario: User = Depends(get_current_user),
):
    if usuario.role != UserRole.SUPERVISOR:
        raise HTTPException(
            status_code=403,
            detail="Somente o supervisor pode excluir itens do cadastro territorial.",
        )
    item = (
        consulta_escopo(db, usuario)
        .filter(CadastroTerritorial.id == territorio_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Cadastro territorial não encontrado")
    db.delete(item)
    db.commit()
    return None
