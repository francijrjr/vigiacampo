from sqlalchemy import Column, String, DateTime
from app.db.session import Base


class SessaoRevogada(Base):
    __tablename__ = "sessoes_revogadas"
    id = Column(String(64), primary_key=True)
    expira_em = Column(DateTime, nullable=False)
