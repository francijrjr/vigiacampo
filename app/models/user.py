from app.core.datas import agora_utc
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class UserRole(str, enum.Enum):
    AGENTE = "AGENTE"
    SUPERVISOR = "SUPERVISOR"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.AGENTE)
    is_active = Column(Boolean, default=True)
    municipio = Column(String(100), nullable=True)
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=agora_utc)
    updated_at = Column(DateTime, default=agora_utc, onupdate=agora_utc)

    supervisor = relationship("User", remote_side=[id], backref="agentes")
    registros = relationship("RegistroDiario", back_populates="agente", foreign_keys="RegistroDiario.agente_id")
