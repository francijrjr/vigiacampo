"""Geometria GeoJSON opcional do quarteirão."""
from alembic import op
import sqlalchemy as sa

revision = '91c02_mapa'
down_revision = '78b01_boletim'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('quarteiroes', sa.Column('geometria', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('quarteiroes', 'geometria')
