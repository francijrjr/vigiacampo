from app.core.datas import agora_utc
import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Enum as SAEnum,
    ForeignKey, Text, Float, UniqueConstraint, JSON
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class StatusRegistro(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_SYNC = "PENDING_SYNC"
    SYNCED = "SYNCED"


class TipoAtividade(str, enum.Enum):
    LI = "LI"
    LI_T = "LI+T"
    PE = "PE"
    PE_T = "PE+T"
    DF = "DF"
    PVE = "PVE"
    OUTROS = "Outros"


class TipoImovel(str, enum.Enum):
    RESIDENCIAL = "RESIDENCIAL"
    COMERCIAL = "COMERCIAL"
    TERRENO = "TERRENO"
    PONTO_ESTRATEGICO = "PONTO_ESTRATEGICO"
    OUTRO = "OUTRO"


class TipoVisita(str, enum.Enum):
    NORMAL = "NORMAL"
    RECUSA = "RECUSA"
    FECHADO = "FECHADO"
    RECUPERADO = "RECUPERADO"


class Pendencia(str, enum.Enum):
    NENHUMA = "NENHUMA"
    FECHADO = "FECHADO"
    RECUSA = "RECUSA"
    OUTRA = "OUTRA"


class CategoriaDeposito(str, enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B = "B"
    C = "C"
    D1 = "D1"
    D2 = "D2"
    E = "E"


class CategoriaTratamento(str, enum.Enum):
    LARVICIDA_1 = "LARVICIDA_1"
    LARVICIDA_2 = "LARVICIDA_2"
    ADULTICIDA = "ADULTICIDA"


class RegistroDiario(Base):
    __tablename__ = "registros_diarios"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)  # para idempotência
    agente_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    municipio = Column(String(100), nullable=False)
    codigo_area = Column(String(50), nullable=False)
    codigo_serie = Column(String(100), nullable=True)
    ciclo = Column(String(50), nullable=False)
    data = Column(Date, nullable=False)
    zona = Column(String(50), nullable=True)
    atividade = Column(SAEnum(TipoAtividade), nullable=False)
    status = Column(SAEnum(StatusRegistro), default=StatusRegistro.DRAFT, nullable=False)
    concluido = Column(Boolean, default=False)
    observacoes = Column(Text, nullable=True)
    synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=agora_utc)
    updated_at = Column(DateTime, default=agora_utc, onupdate=agora_utc)

    agente = relationship("User", back_populates="registros", foreign_keys=[agente_id])
    quarteiroes = relationship("Quarteirao", back_populates="registro", cascade="all, delete-orphan")
    imoveis = relationship("Imovel", back_populates="registro", cascade="all, delete-orphan")

    # Resumos calculados (verso da ficha)
    resumo_imoveis_trabalhados = Column(Integer, default=0)
    resumo_pendencias = Column(Integer, default=0)
    resumo_depositos_inspecionados = Column(Integer, default=0)
    resumo_imoveis_com_especimes = Column(Integer, default=0)
    resumo_totais_tratamento = Column(Integer, default=0)
    resumo_exemplares = Column(Integer, default=0)


class Quarteirao(Base):
    __tablename__ = "quarteiroes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    registro_id = Column(Integer, ForeignKey("registros_diarios.id"), nullable=False, index=True)
    numero = Column(String(20), nullable=False)
    sequencia = Column(Integer, nullable=True)
    lado = Column(String(20), nullable=True)
    logradouro = Column(String(255), nullable=True)
    geometria = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=agora_utc)

    registro = relationship("RegistroDiario", back_populates="quarteiroes")
    imoveis = relationship("Imovel", back_populates="quarteirao")
    boletim = relationship("BoletimReconhecimento", back_populates="quarteirao", uselist=False, cascade="all, delete-orphan")


class Imovel(Base):
    __tablename__ = "imoveis"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    registro_id = Column(Integer, ForeignKey("registros_diarios.id"), nullable=False, index=True)
    quarteirao_id = Column(Integer, ForeignKey("quarteiroes.id"), nullable=True)
    numero = Column(String(20), nullable=False)
    complemento = Column(String(100), nullable=True)
    logradouro = Column(String(255), nullable=True)
    lado = Column(String(20), nullable=True)
    tipo = Column(SAEnum(TipoImovel), default=TipoImovel.RESIDENCIAL)
    hora_entrada = Column(String(10), nullable=True)  # HH:MM
    tipo_visita = Column(SAEnum(TipoVisita), default=TipoVisita.NORMAL)
    pendencia = Column(SAEnum(Pendencia), default=Pendencia.NENHUMA)
    created_at = Column(DateTime, default=agora_utc)
    updated_at = Column(DateTime, default=agora_utc, onupdate=agora_utc)

    registro = relationship("RegistroDiario", back_populates="imoveis")
    quarteirao = relationship("Quarteirao", back_populates="imoveis")
    inspecoes = relationship("Inspecao", back_populates="imovel", cascade="all, delete-orphan")
    coletas = relationship("Coleta", back_populates="imovel", cascade="all, delete-orphan")
    especimes = relationship("Especime", back_populates="imovel", cascade="all, delete-orphan")
    tratamentos = relationship("Tratamento", back_populates="imovel", cascade="all, delete-orphan")
    depositos_eliminados = relationship("DepositoEliminado", back_populates="imovel", cascade="all, delete-orphan")
    fotos = relationship("Foto", back_populates="imovel", cascade="all, delete-orphan")


class Inspecao(Base):
    __tablename__ = "inspecoes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False, index=True)
    a1 = Column(Integer, default=0)
    a2 = Column(Integer, default=0)
    b = Column(Integer, default=0)
    c = Column(Integer, default=0)
    d1 = Column(Integer, default=0)
    d2 = Column(Integer, default=0)
    e = Column(Integer, default=0)
    total = Column(Integer, default=0)  # calculado
    created_at = Column(DateTime, default=agora_utc)

    imovel = relationship("Imovel", back_populates="inspecoes")


class Coleta(Base):
    __tablename__ = "coletas"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False, index=True)
    numero_amostra = Column(String(50), nullable=False)
    tubito_inicial = Column(Integer, nullable=False)
    tubito_final = Column(Integer, nullable=False)
    quantidade_tubitos = Column(Integer, default=0)  # calculado
    created_at = Column(DateTime, default=agora_utc)

    imovel = relationship("Imovel", back_populates="coletas")


class Especime(Base):
    __tablename__ = "especimes"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False, index=True)
    especie = Column(String(100), nullable=False)
    larvas = Column(Integer, default=0)
    pupas = Column(Integer, default=0)
    pupa_aedes = Column(Integer, default=0)
    adultos = Column(Integer, default=0)
    created_at = Column(DateTime, default=agora_utc)

    imovel = relationship("Imovel", back_populates="especimes")


class Tratamento(Base):
    __tablename__ = "tratamentos"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False, index=True)
    categoria = Column(SAEnum(CategoriaTratamento), nullable=False)
    produto = Column(String(100), nullable=True)
    quantidade = Column(Float, default=0)
    depositos_tratados = Column(Integer, default=0)
    cargas = Column(Integer, default=0)
    created_at = Column(DateTime, default=agora_utc)

    imovel = relationship("Imovel", back_populates="tratamentos")


class DepositoEliminado(Base):
    __tablename__ = "depositos_eliminados"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False, index=True)
    tipo = Column(String(50), nullable=False)
    quantidade = Column(Integer, default=0)
    created_at = Column(DateTime, default=agora_utc)

    imovel = relationship("Imovel", back_populates="depositos_eliminados")


class Foto(Base):
    __tablename__ = "fotos"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(64), unique=True, index=True, nullable=True)
    imovel_id = Column(Integer, ForeignKey("imoveis.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    descricao = Column(String(500), nullable=True)
    data_hora = Column(DateTime, default=agora_utc)
    created_at = Column(DateTime, default=agora_utc)

    imovel = relationship("Imovel", back_populates="fotos")
