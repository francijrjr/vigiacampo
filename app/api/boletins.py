from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.registro import RegistroDiario, Quarteirao
from app.models.boletim import BoletimReconhecimento
from app.schemas.boletim import BoletimCreate, BoletimDados, BoletimResponse
from app.services.permissoes import pode_acessar, exigir_edicao
from app.services.boletim import montar_boletim

router=APIRouter(prefix='/registros/{registro_id}/boletins',tags=['Boletim de Reconhecimento'])


def obter_registro(db, usuario, registro_id, editar=False):
    registro=db.get(RegistroDiario,registro_id)
    if not registro:
        raise HTTPException(404,'Registro não encontrado')
    if not pode_acessar(usuario,registro):
        raise HTTPException(403,'Você não tem acesso a este registro')
    if editar:
        exigir_edicao(usuario,registro)
    return registro


def obter_boletim(db, usuario, registro_id, boletim_id, editar=False):
    obter_registro(db,usuario,registro_id,editar)
    boletim=db.query(BoletimReconhecimento).join(Quarteirao).filter(
        BoletimReconhecimento.id==boletim_id,Quarteirao.registro_id==registro_id).first()
    if not boletim:
        raise HTTPException(404,'Boletim não encontrado neste registro')
    return boletim


@router.get('',response_model=list[BoletimResponse],summary='Listar boletins do registro')
def listar(registro_id:int,db:Session=Depends(get_db),usuario=Depends(get_current_user)):
    obter_registro(db,usuario,registro_id)
    itens=db.query(BoletimReconhecimento).join(Quarteirao).filter(Quarteirao.registro_id==registro_id).order_by(BoletimReconhecimento.id).all()
    return [montar_boletim(item,usuario) for item in itens]


@router.post('',response_model=BoletimResponse,status_code=201,summary='Criar boletim de reconhecimento',
             description='Preenche o cabeçalho da ficha e cria ou vincula um quarteirão. Os imóveis desse quarteirão compõem o boletim e seu fechamento.')
def criar(registro_id:int,payload:BoletimCreate,db:Session=Depends(get_db),usuario=Depends(get_current_user)):
    obter_registro(db,usuario,registro_id,True)
    if payload.quarteirao_id:
        q=db.query(Quarteirao).filter_by(id=payload.quarteirao_id,registro_id=registro_id).first()
        if not q:
            raise HTTPException(422,'O quarteirão deve pertencer a este registro')
        if q.numero!=payload.quarteirao_numero:
            raise HTTPException(422,'O número informado deve corresponder ao quarteirão escolhido')
    else:
        existentes=db.query(Quarteirao).filter_by(registro_id=registro_id,numero=payload.quarteirao_numero).all()
        if len(existentes)>1:
            raise HTTPException(409,'Há mais de um quarteirão com este número. Escolha o quarteirão pelo identificador.')
        q=existentes[0] if existentes else Quarteirao(registro_id=registro_id,numero=payload.quarteirao_numero)
        db.add(q)
        db.flush()
    if q.boletim:
        raise HTTPException(409,'Este quarteirão já tem um boletim. Abra o boletim existente para editar.')
    dados=payload.model_dump(exclude={'quarteirao_numero','quarteirao_id'})
    boletim=BoletimReconhecimento(quarteirao_id=q.id,**dados)
    db.add(boletim)
    db.commit()
    return montar_boletim(boletim,usuario)


@router.get('/{boletim_id}',response_model=BoletimResponse,summary='Abrir boletim com imóveis e fechamento')
def abrir(registro_id:int,boletim_id:int,db:Session=Depends(get_db),usuario=Depends(get_current_user)):
    return montar_boletim(obter_boletim(db,usuario,registro_id,boletim_id),usuario)


@router.put('/{boletim_id}',response_model=BoletimResponse,summary='Atualizar cabeçalho do boletim')
def editar(registro_id:int,boletim_id:int,payload:BoletimDados,db:Session=Depends(get_db),usuario=Depends(get_current_user)):
    boletim=obter_boletim(db,usuario,registro_id,boletim_id,True)
    q=boletim.quarteirao
    if db.query(Quarteirao).filter(Quarteirao.registro_id==registro_id,Quarteirao.numero==payload.quarteirao_numero,Quarteirao.id!=q.id).first():
        raise HTTPException(409,'Já existe outro quarteirão com este número neste registro')
    q.numero=payload.quarteirao_numero
    for campo,valor in payload.model_dump(exclude={'quarteirao_numero'}).items():
        setattr(boletim,campo,valor)
    db.commit()
    return montar_boletim(boletim,usuario)


@router.get('/{boletim_id}/pdf',summary='Baixar boletim para impressão',
            response_class=Response,responses={200:{'content':{'application/pdf':{}}}},
            description='Gera a ficha em A4 com duas colunas, fechamento por tipo, nome e espaço para assinatura. Disponível ao agente responsável e ao supervisor da equipe.')
def pdf(registro_id:int,boletim_id:int,db:Session=Depends(get_db),usuario=Depends(get_current_user)):
    from app.services.boletim_pdf import gerar_boletim_pdf
    dados=montar_boletim(obter_boletim(db,usuario,registro_id,boletim_id),usuario)
    return Response(gerar_boletim_pdf(dados),media_type='application/pdf',
        headers={'Content-Disposition':f'attachment; filename="boletim-{boletim_id}.pdf"'})
