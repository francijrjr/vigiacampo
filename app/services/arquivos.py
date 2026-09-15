import logging
from pathlib import Path
from sqlalchemy import event
from sqlalchemy.orm import Session
from app.models.registro import Foto
from app.core.config import settings


@event.listens_for(Session, "before_flush")
def anotar_fotos_excluidas(sessao, contexto, instancias):
    caminhos = sessao.info.setdefault("fotos_excluidas", set())
    caminhos.update(foto.filepath for foto in sessao.deleted if isinstance(foto, Foto))


@event.listens_for(Session, "after_commit")
def remover_arquivos_excluidos(sessao):
    raiz = Path(settings.UPLOAD_DIR).resolve()
    for nome in sessao.info.pop("fotos_excluidas", set()):
        caminho = Path(nome).resolve()
        if caminho.is_relative_to(raiz) and caminho != raiz:
            try:
                caminho.unlink(missing_ok=True)
            except OSError:
                logging.getLogger(__name__).exception("Não foi possível remover a foto excluída")


@event.listens_for(Session, "after_rollback")
def cancelar_exclusao(sessao):
    sessao.info.pop("fotos_excluidas", None)
