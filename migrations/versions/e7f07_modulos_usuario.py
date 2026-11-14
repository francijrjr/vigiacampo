"""Adiciona módulos habilitados por usuário."""
from alembic import op
import sqlalchemy as sa


revision = "e7f07_modulos_usuario"
down_revision = "d6e06_cadastro_territorial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("modulos", sa.JSON(), nullable=True))
    op.execute("UPDATE users SET modulos = '[\"reconhecimento\", \"vetorial\"]' WHERE modulos IS NULL")


def downgrade():
    op.drop_column("users", "modulos")
