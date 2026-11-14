"""Cadastro territorial do módulo de Reconhecimento Geográfico."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.core.datas import agora_utc


class CadastroTerritorial(Base):
    __tablename__ = "cadastros_territoriais"

    id = Column(Integer, primary_key=True, index=True)
    criado_por_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    municipio = Column(String(100), nullable=False)
    distrito = Column(String(100), nullable=True)
    codigo_localidade = Column(String(50), nullable=True)
    localidade = Column(String(150), nullable=False)
    categoria = Column(String(50), nullable=False, default="Urbana")
    zona = Column(String(50), nullable=True)
    quarteirao_numero = Column(String(20), nullable=False)
    lados = Column(Integer, default=4, nullable=False)
    logradouros = Column(String(500), nullable=True)
    residenciais = Column(Integer, default=0, nullable=False)
    comerciais = Column(Integer, default=0, nullable=False)
    terrenos_baldios = Column(Integer, default=0, nullable=False)
    pontos_estrategicos = Column(Integer, default=0, nullable=False)
    outros = Column(Integer, default=0, nullable=False)
    total_imoveis = Column(Integer, default=0, nullable=False)
    geometria = Column(JSON, nullable=True)
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=agora_utc, nullable=False)
    updated_at = Column(DateTime, default=agora_utc, onupdate=agora_utc, nullable=False)

    criado_por = relationship("User")
