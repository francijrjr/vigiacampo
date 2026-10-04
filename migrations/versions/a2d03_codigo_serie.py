"""Código de série dos registros diários; registros antigos mantêm valor vazio."""
from alembic import op
import sqlalchemy as sa

revision = 'a2d03_serie'
down_revision = '91c02_mapa'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('registros_diarios', sa.Column('codigo_serie', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('registros_diarios', 'codigo_serie')
