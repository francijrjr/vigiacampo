"""Manutenção dos quarteirões, imóveis e dados coletados na visita."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.registro import RegistroDiario, Quarteirao, Imovel, Inspecao, Coleta, Especime, Tratamento, DepositoEliminado
from app.schemas.registro import (QuarteiraoCreate, QuarteiraoResponse, InspecaoCreate, InspecaoResponse,
    ColetaCreate, ColetaResponse, EspecimeCreate, EspecimeResponse, TratamentoCreate, TratamentoResponse,
    DepositoEliminadoCreate, DepositoEliminadoResponse)
from app.services.permissoes import exigir_edicao, pode_acessar
from app.services.resumo import recalcular_resumos

router = APIRouter(prefix="/registros", tags=["Dados das visitas"])


def registro_editavel(db, usuario, registro_id):
    registro = db.get(RegistroDiario, registro_id)
    if not registro:
        raise HTTPException(404, "Registro não encontrado")
    exigir_edicao(usuario, registro)
    return registro


@router.delete("/{registro_id}", status_code=204, summary="Excluir registro e suas visitas")
def excluir_registro(registro_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    registro = registro_editavel(db, usuario, registro_id)
    db.delete(registro)
    db.commit()
    return Response(status_code=204)


@router.get("/{registro_id}/quarteiroes", response_model=list[QuarteiraoResponse], summary="Listar quarteirões")
def listar_quarteiroes(registro_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    registro = db.get(RegistroDiario, registro_id)
    if not registro:
        raise HTTPException(404, "Registro não encontrado")
    if not pode_acessar(usuario, registro):
        raise HTTPException(403, "Acesso negado")
    return registro.quarteiroes


@router.put("/{registro_id}/quarteiroes/{quarteirao_id}", response_model=QuarteiraoResponse, summary="Editar quarteirão")
def editar_quarteirao(registro_id: int, quarteirao_id: int, payload: QuarteiraoCreate,
                     db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    registro_editavel(db, usuario, registro_id)
    item = db.query(Quarteirao).filter_by(id=quarteirao_id, registro_id=registro_id).first()
    if not item:
        raise HTTPException(404, "Quarteirão não encontrado")
    campos = payload.model_dump(exclude={"client_id"})
    if 'geometria' not in payload.model_fields_set:
        campos.pop('geometria', None)
    for campo, valor in campos.items():
        setattr(item, campo, valor)
    db.commit()
    return item


@router.delete("/{registro_id}/quarteiroes/{quarteirao_id}", status_code=204, summary="Excluir quarteirão vazio")
def excluir_quarteirao(registro_id: int, quarteirao_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    registro_editavel(db, usuario, registro_id)
    item = db.query(Quarteirao).filter_by(id=quarteirao_id, registro_id=registro_id).first()
    if not item:
        raise HTTPException(404, "Quarteirão não encontrado")
    if item.imoveis:
        raise HTTPException(409, "Mova ou exclua os imóveis deste quarteirão primeiro")
    db.delete(item)
    db.commit()
    return Response(status_code=204)


@router.delete("/{registro_id}/imoveis/{imovel_id}", status_code=204, summary="Excluir imóvel e dados da visita")
def excluir_imovel(registro_id: int, imovel_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    registro = registro_editavel(db, usuario, registro_id)
    item = db.query(Imovel).filter_by(id=imovel_id, registro_id=registro_id).first()
    if not item:
        raise HTTPException(404, "Imóvel não encontrado")
    db.delete(item)
    db.flush()
    recalcular_resumos(db, registro)
    db.commit()
    return Response(status_code=204)


def registrar_rotas(nome, modelo, entrada, saida):
    """As cinco coleções da visita compartilham as mesmas regras de acesso."""
    caminho = "/{registro_id}/imoveis/{imovel_id}/" + nome

    def localizar(db, usuario, registro_id, imovel_id, editar=False):
        registro = db.get(RegistroDiario, registro_id)
        if not registro or not db.query(Imovel).filter_by(id=imovel_id, registro_id=registro_id).first():
            raise HTTPException(404, "Imóvel não encontrado neste registro")
        if not pode_acessar(usuario, registro):
            raise HTTPException(403, "Acesso negado")
        if editar:
            exigir_edicao(usuario, registro)
        return registro

    def listar(registro_id: int, imovel_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
        localizar(db, usuario, registro_id, imovel_id)
        return db.query(modelo).filter_by(imovel_id=imovel_id).all()

    def criar(registro_id: int, imovel_id: int, payload: entrada, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
        registro = localizar(db, usuario, registro_id, imovel_id, True)
        item = modelo(imovel_id=imovel_id, **payload.model_dump())
        db.add(item)
        db.flush()
        db.expire_all()
        recalcular_resumos(db, registro)
        db.commit()
        return item

    def editar(registro_id: int, imovel_id: int, item_id: int, payload: entrada, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
        registro = localizar(db, usuario, registro_id, imovel_id, True)
        item = db.query(modelo).filter_by(id=item_id, imovel_id=imovel_id).first()
        if not item:
            raise HTTPException(404, "Item não encontrado")
        for campo, valor in payload.model_dump(exclude={"client_id"}).items():
            setattr(item, campo, valor)
        db.flush()
        db.expire_all()
        recalcular_resumos(db, registro)
        db.commit()
        return item

    def excluir(registro_id: int, imovel_id: int, item_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
        registro = localizar(db, usuario, registro_id, imovel_id, True)
        item = db.query(modelo).filter_by(id=item_id, imovel_id=imovel_id).first()
        if not item:
            raise HTTPException(404, "Item não encontrado")
        db.delete(item)
        db.flush()
        db.expire_all()
        recalcular_resumos(db, registro)
        db.commit()
        return Response(status_code=204)

    for metodo, funcao, rota, resposta, codigo in [
        ("GET", listar, caminho, list[saida], 200), ("POST", criar, caminho, saida, 201),
        ("PUT", editar, caminho+"/{item_id}", saida, 200), ("DELETE", excluir, caminho+"/{item_id}", None, 204)]:
        router.add_api_route(rota, funcao, methods=[metodo], response_model=resposta,
                            status_code=codigo, summary=f"{funcao.__name__.capitalize()} {nome}",
                            name=f"{funcao.__name__}_{nome}")


for definicao in [("inspecoes", Inspecao, InspecaoCreate, InspecaoResponse),
                  ("coletas", Coleta, ColetaCreate, ColetaResponse),
                  ("especimes", Especime, EspecimeCreate, EspecimeResponse),
                  ("tratamentos", Tratamento, TratamentoCreate, TratamentoResponse),
                  ("depositos-eliminados", DepositoEliminado, DepositoEliminadoCreate, DepositoEliminadoResponse)]:
    registrar_rotas(*definicao)
