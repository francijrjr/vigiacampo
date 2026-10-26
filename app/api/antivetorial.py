from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.registro import RegistroDiario
from app.schemas.registro import AntivetorialDados
from app.services.permissoes import pode_acessar,exigir_edicao
from app.services.antivetorial_pdf import gerar_pdf_antivetorial
router = APIRouter(prefix="/registros", tags=["Serviço Antivetorial"])


def obter(id, db, u):
    registro = db.get(RegistroDiario, id)
    if not registro:
        raise HTTPException(404, "Registro não encontrado")
    if not pode_acessar(u, registro):
        raise HTTPException(403, "Você não tem acesso a este registro")
    return registro


@router.get("/{registro_id}/antivetorial")
def consultar(registro_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    return obter(registro_id, db, usuario).antivetorial or {}


@router.put("/{registro_id}/antivetorial")
def salvar(registro_id: int, payload: AntivetorialDados, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    registro = obter(registro_id, db, usuario)
    exigir_edicao(usuario, registro)
    registro.antivetorial = payload.model_dump(mode="json")
    db.commit()
    return registro.antivetorial


@router.get("/{registro_id}/antivetorial/pdf")
def pdf(registro_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    registro = obter(registro_id, db, usuario)
    return StreamingResponse(
        gerar_pdf_antivetorial(registro, registro.antivetorial or {}),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="registro-antivetorial-{registro_id}.pdf"'},
    )
