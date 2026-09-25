"""Criação, cópia e consultas de registros diários.

Os serviços usam flush para preparar os dados. O commit fica nas rotas,
permitindo que a sincronização confirme ou reverta o lote inteiro.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session, joinedload

from app.core.datas import agora_utc
from app.models.boletim import BoletimReconhecimento
from app.models.registro import (
    RegistroDiario, Quarteirao, Imovel, Inspecao, Coleta,
    Especime, Tratamento, DepositoEliminado, StatusRegistro,
)
from app.models.user import User
from app.schemas.registro import ImovelCreate, RegistroDiarioCreate
from app.services.resumo import recalcular_resumos


RELACOES_VISITA = (
    Imovel.inspecoes,
    Imovel.coletas,
    Imovel.especimes,
    Imovel.tratamentos,
    Imovel.depositos_eliminados,
    Imovel.fotos,
)


def consultar_imoveis_completos(db: Session) -> Query:
    return db.query(Imovel).options(
        *(joinedload(relacao) for relacao in RELACOES_VISITA)
    )


def consultar_registros_completos(db: Session) -> Query:
    return db.query(RegistroDiario).options(
        joinedload(RegistroDiario.quarteiroes),
        *(
            joinedload(RegistroDiario.imoveis).joinedload(relacao)
            for relacao in RELACOES_VISITA
        ),
    )


def criar_imovel(db: Session, registro_id: int, dados_imovel: ImovelCreate) -> Imovel:
    """Salva o imóvel e suas visitas, validando o vínculo com o quarteirão."""
    quarteirao_id = dados_imovel.quarteirao_id
    if dados_imovel.quarteirao_client_id:
        quarteirao = db.query(Quarteirao).filter_by(
            client_id=dados_imovel.quarteirao_client_id,
            registro_id=registro_id,
        ).first()
        if not quarteirao:
            raise HTTPException(422, "Quarteirão offline não encontrado neste registro")
        if dados_imovel.quarteirao_id and dados_imovel.quarteirao_id != quarteirao.id:
            raise HTTPException(422, "Os identificadores do quarteirão não correspondem")
        quarteirao_id = quarteirao.id
    if quarteirao_id and not db.query(Quarteirao).filter_by(
        id=quarteirao_id, registro_id=registro_id
    ).first():
        raise HTTPException(422, "O quarteirão deve pertencer ao mesmo registro")
    imovel = Imovel(
        client_id=dados_imovel.client_id,
        registro_id=registro_id,
        quarteirao_id=quarteirao_id,
        numero=dados_imovel.numero,
        complemento=dados_imovel.complemento,
        logradouro=dados_imovel.logradouro,
        lado=dados_imovel.lado,
        tipo=dados_imovel.tipo,
        hora_entrada=dados_imovel.hora_entrada,
        tipo_visita=dados_imovel.tipo_visita,
        pendencia=dados_imovel.pendencia,
    )
    db.add(imovel)
    db.flush()

    for inspecao in dados_imovel.inspecoes:
        total = (
            inspecao.a1 + inspecao.a2 + inspecao.b + inspecao.c
            + inspecao.d1 + inspecao.d2 + inspecao.e
        )
        db.add(Inspecao(
            client_id=inspecao.client_id,
            imovel_id=imovel.id,
            a1=inspecao.a1, a2=inspecao.a2, b=inspecao.b, c=inspecao.c,
            d1=inspecao.d1, d2=inspecao.d2, e=inspecao.e, total=total,
        ))
    for coleta in dados_imovel.coletas:
        quantidade = max(0, coleta.tubito_final - coleta.tubito_inicial + 1)
        db.add(Coleta(
            client_id=coleta.client_id,
            imovel_id=imovel.id,
            numero_amostra=coleta.numero_amostra,
            tubito_inicial=coleta.tubito_inicial,
            tubito_final=coleta.tubito_final,
            quantidade_tubitos=quantidade,
        ))
    for especime in dados_imovel.especimes:
        db.add(Especime(
            client_id=especime.client_id,
            imovel_id=imovel.id,
            especie=especime.especie,
            larvas=especime.larvas, pupas=especime.pupas,
            pupa_aedes=especime.pupa_aedes, adultos=especime.adultos,
        ))
    for tratamento in dados_imovel.tratamentos:
        db.add(Tratamento(
            client_id=tratamento.client_id,
            imovel_id=imovel.id,
            categoria=tratamento.categoria,
            produto=tratamento.produto,
            quantidade=tratamento.quantidade,
            depositos_tratados=tratamento.depositos_tratados,
            cargas=tratamento.cargas,
        ))
    for deposito in dados_imovel.depositos_eliminados:
        db.add(DepositoEliminado(
            client_id=deposito.client_id,
            imovel_id=imovel.id,
            tipo=deposito.tipo,
            quantidade=deposito.quantidade,
        ))
    return imovel



def criar_registro(
    db: Session, payload: RegistroDiarioCreate, agente_id: int, *, sincronizado: bool = False
) -> RegistroDiario:
    """Prepara registro e visitas; a rota confirma a transação completa."""
    registro = RegistroDiario(
        client_id=payload.client_id,
        agente_id=agente_id,
        municipio=payload.municipio,
        codigo_area=payload.codigo_area,
        ciclo=payload.ciclo,
        data=payload.data,
        zona=payload.zona,
        atividade=payload.atividade,
        concluido=True if sincronizado else payload.concluido,
        observacoes=payload.observacoes,
        status=StatusRegistro.SYNCED if sincronizado else StatusRegistro.DRAFT,
        synced_at=agora_utc() if sincronizado else None,
    )
    db.add(registro)
    db.flush()

    for quarteirao in payload.quarteiroes:
        db.add(Quarteirao(
            client_id=quarteirao.client_id,
            registro_id=registro.id,
            numero=quarteirao.numero,
            sequencia=quarteirao.sequencia,
            lado=quarteirao.lado,
            logradouro=quarteirao.logradouro,
        ))
    db.flush()

    for dados_imovel in payload.imoveis:
        criar_imovel(db, registro.id, dados_imovel)

    db.flush()
    recalcular_resumos(db, registro)
    return registro


def copiar_registro(db: Session, original: RegistroDiario, usuario: User) -> RegistroDiario:
    """Copia visitas e boletins para um rascunho de hoje, sem fotos ou client_id."""
    novo = RegistroDiario(
        agente_id=usuario.id,
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

    quarteiroes_copiados = {}
    for quarteirao in original.quarteiroes:
        copia_quarteirao = Quarteirao(
            registro_id=novo.id,
            numero=quarteirao.numero,
            sequencia=quarteirao.sequencia,
            lado=quarteirao.lado,
            logradouro=quarteirao.logradouro,
        )
        db.add(copia_quarteirao)
        db.flush()
        quarteiroes_copiados[quarteirao.id] = copia_quarteirao.id
        if quarteirao.boletim:
            cabecalho = {campo: getattr(quarteirao.boletim, campo) for campo in (
                'uf', 'distrito', 'municipio', 'localidade', 'subdistrito', 'sublocal', 'categoria', 'funcao_responsavel')}
            db.add(BoletimReconhecimento(quarteirao_id=copia_quarteirao.id, responsavel=usuario.full_name,
                                         data=novo.data, **cabecalho))

    for dados_imovel in original.imoveis:
        imovel = Imovel(
            registro_id=novo.id,
            quarteirao_id=quarteiroes_copiados.get(dados_imovel.quarteirao_id) if dados_imovel.quarteirao_id else None,
            numero=dados_imovel.numero,
            complemento=dados_imovel.complemento,
            logradouro=dados_imovel.logradouro,
            lado=dados_imovel.lado,
            tipo=dados_imovel.tipo,
            hora_entrada=dados_imovel.hora_entrada,
            tipo_visita=dados_imovel.tipo_visita,
            pendencia=dados_imovel.pendencia,
        )
        db.add(imovel)
        db.flush()
        for inspecao in dados_imovel.inspecoes:
            db.add(Inspecao(
                imovel_id=imovel.id, a1=inspecao.a1, a2=inspecao.a2, b=inspecao.b, c=inspecao.c,
                d1=inspecao.d1, d2=inspecao.d2, e=inspecao.e, total=inspecao.total,
            ))
        for coleta in dados_imovel.coletas:
            db.add(Coleta(
                imovel_id=imovel.id, numero_amostra=coleta.numero_amostra,
                tubito_inicial=coleta.tubito_inicial, tubito_final=coleta.tubito_final,
                quantidade_tubitos=coleta.quantidade_tubitos,
            ))
        for especime in dados_imovel.especimes:
            db.add(Especime(
                imovel_id=imovel.id, especie=especime.especie,
                larvas=especime.larvas, pupas=especime.pupas, pupa_aedes=especime.pupa_aedes, adultos=especime.adultos,
            ))
        for tratamento in dados_imovel.tratamentos:
            db.add(Tratamento(
                imovel_id=imovel.id, categoria=tratamento.categoria, produto=tratamento.produto,
                quantidade=tratamento.quantidade, depositos_tratados=tratamento.depositos_tratados, cargas=tratamento.cargas,
            ))
        for deposito in dados_imovel.depositos_eliminados:
            db.add(DepositoEliminado(imovel_id=imovel.id, tipo=deposito.tipo, quantidade=deposito.quantidade))

    db.flush()
    recalcular_resumos(db, novo)
    return novo
