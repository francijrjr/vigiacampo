"""Cria o cadastro territorial permanente."""
from alembic import op
import sqlalchemy as sa


revision = "d6e06_cadastro_territorial"
down_revision = "c4d05_lado_numerico"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cadastros_territoriais",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criado_por_id", sa.Integer(), nullable=False),
        sa.Column("municipio", sa.String(length=100), nullable=False),
        sa.Column("distrito", sa.String(length=100), nullable=True),
        sa.Column("codigo_localidade", sa.String(length=50), nullable=True),
        sa.Column("localidade", sa.String(length=150), nullable=False),
        sa.Column("categoria", sa.String(length=50), nullable=False, server_default="Urbana"),
        sa.Column("zona", sa.String(length=50), nullable=True),
        sa.Column("quarteirao_numero", sa.String(length=20), nullable=False),
        sa.Column("lados", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("logradouros", sa.String(length=500), nullable=True),
        sa.Column("residenciais", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comerciais", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("terrenos_baldios", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pontos_estrategicos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("outros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_imoveis", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("geometria", sa.JSON(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["criado_por_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cadastros_territoriais_criado_por_id", "cadastros_territoriais", ["criado_por_id"])
    op.create_index("ix_cadastros_territoriais_id", "cadastros_territoriais", ["id"])


def downgrade():
    op.drop_index("ix_cadastros_territoriais_id", table_name="cadastros_territoriais")
    op.drop_index("ix_cadastros_territoriais_criado_por_id", table_name="cadastros_territoriais")
    op.drop_table("cadastros_territoriais")
