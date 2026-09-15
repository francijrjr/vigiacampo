from app.core.datas import agora_utc
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.registro import RegistroDiario, Imovel, Foto
from app.schemas.registro import FotoResponse
from app.core.security import get_current_user
from app.core.config import settings
from app.services.permissoes import pode_acessar, exigir_edicao
from fastapi.responses import FileResponse, Response
from PIL import Image, UnidentifiedImageError
from io import BytesIO

router = APIRouter(prefix="/fotos", tags=["Fotos"])

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def _can_access_imovel(user: User, imovel: Imovel, db: Session) -> bool:
    registro = db.query(RegistroDiario).filter(RegistroDiario.id == imovel.registro_id).first()
    if not registro:
        return False
    return pode_acessar(user, registro)


@router.post(
    "/imovel/{imovel_id}",
    response_model=FotoResponse,
    status_code=201,
    summary="Upload de foto",
    description="RF21 - Upload de foto vinculada a um imóvel (evidência/auditoria).",
)
async def upload_foto(
    imovel_id: int,
    file: UploadFile = File(...),
    descricao: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    if not _can_access_imovel(current_user, imovel, db):
        raise HTTPException(status_code=403, detail="Acesso negado")

    exigir_edicao(current_user, imovel.registro)
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=400, detail=f"Arquivo excede {settings.MAX_UPLOAD_SIZE_MB}MB")
    try:
        imagem = Image.open(BytesIO(content))
        if imagem.format not in {"JPEG", "PNG", "WEBP"} or imagem.width * imagem.height > 25_000_000:
            raise ValueError()
        imagem.verify()
        imagem = Image.open(BytesIO(content)).convert("RGB")
        destino = BytesIO()
        imagem.save(destino, format="JPEG", quality=88)
        content = destino.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422, "Envie uma imagem JPEG, PNG ou WebP válida, de até 25 milhões de pixels")
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)

    foto = Foto(
        imovel_id=imovel_id,
        filename=filename,
        filepath=filepath,
        descricao=descricao,
        data_hora=agora_utc(),
    )
    db.add(foto)
    try:
        db.commit()
    except Exception:
        db.rollback()
        os.remove(filepath)
        raise
    db.refresh(foto)
    return foto


@router.get(
    "/imovel/{imovel_id}",
    response_model=List[FotoResponse],
    summary="Listar fotos do imóvel",
    description="RF23",
)
def list_fotos(
    imovel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    imovel = db.query(Imovel).filter(Imovel.id == imovel_id).first()
    if not imovel:
        raise HTTPException(status_code=404, detail="Imóvel não encontrado")
    if not _can_access_imovel(current_user, imovel, db):
        raise HTTPException(status_code=403, detail="Acesso negado")
    return db.query(Foto).filter(Foto.imovel_id == imovel_id).all()


def obter_foto(foto_id, db, usuario):
    foto = db.get(Foto, foto_id)
    if not foto:
        raise HTTPException(404, "Foto não encontrada")
    if not _can_access_imovel(usuario, foto.imovel, db):
        raise HTTPException(403, "Acesso negado")
    return foto


@router.get("/{foto_id}/arquivo", summary="Abrir foto com acesso protegido", response_class=FileResponse)
def abrir_foto(foto_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    foto = obter_foto(foto_id, db, usuario)
    if not os.path.isfile(foto.filepath):
        raise HTTPException(404, "Arquivo não encontrado")
    return FileResponse(foto.filepath, media_type="image/jpeg")


@router.delete("/{foto_id}", status_code=204, summary="Excluir foto")
def excluir_foto(foto_id: int, db: Session = Depends(get_db), usuario=Depends(get_current_user)):
    foto = obter_foto(foto_id, db, usuario)
    exigir_edicao(usuario, foto.imovel.registro)
    db.delete(foto)
    db.commit()
    return Response(status_code=204)
