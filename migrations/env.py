"""Migrações usam a mesma configuração de banco da API."""
from alembic import context
from app.db.session import Base, engine
from app.core.config import settings
import app.models
import app.models.sessao

if context.is_offline_mode():
    context.configure(url=settings.DATABASE_URL, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
