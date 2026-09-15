from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
import sqlite3
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


@event.listens_for(Engine, "connect")
def ativar_integridade_sqlite(conexao, registro):
    if isinstance(conexao, sqlite3.Connection):
        conexao.execute("PRAGMA foreign_keys=ON")

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
