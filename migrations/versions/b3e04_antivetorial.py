"""Ficha do serviço antivetorial vinculada ao registro diário."""
from alembic import op
import sqlalchemy as sa
revision='b3e04_antivetorial'
down_revision='a2d03_serie'
branch_labels=None
depends_on=None
def upgrade(): op.add_column('registros_diarios',sa.Column('antivetorial',sa.JSON(),nullable=True))
def downgrade(): op.drop_column('registros_diarios','antivetorial')
