"""O boletim pertence a um quarteirão e usa os mesmos imóveis das visitas."""
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.core.datas import agora_utc


class BoletimReconhecimento(Base):
    __tablename__ = 'boletins_reconhecimento'

    id = Column(Integer, primary_key=True)
    quarteirao_id = Column(Integer, ForeignKey('quarteiroes.id'), nullable=False, unique=True)
    uf = Column(String(2), nullable=False)
    distrito = Column(String(100), nullable=False)
    municipio = Column(String(100), nullable=False)
    localidade = Column(String(150), nullable=False)
    responsavel = Column(String(150), nullable=False)
    funcao_responsavel = Column(String(30), nullable=False)
    subdistrito = Column(String(100), nullable=True)
    sublocal = Column(String(150), nullable=True)
    categoria = Column(String(50), nullable=False)
    data = Column(Date, nullable=False)
    created_at = Column(DateTime, default=agora_utc, nullable=False)
    updated_at = Column(DateTime, default=agora_utc, onupdate=agora_utc, nullable=False)

    quarteirao = relationship('Quarteirao', back_populates='boletim')
