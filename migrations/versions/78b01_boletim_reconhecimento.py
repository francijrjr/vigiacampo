"""Boletim de reconhecimento e endereço por imóvel."""
from alembic import op
import sqlalchemy as sa

revision='78b01_boletim'
down_revision='0bc1e56c298d'
branch_labels=None
depends_on=None


def upgrade():
    op.add_column('imoveis',sa.Column('logradouro',sa.String(255),nullable=True))
    op.add_column('imoveis',sa.Column('lado',sa.String(20),nullable=True))
    if op.get_bind().dialect.name=='postgresql':
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE tipoimovel ADD VALUE IF NOT EXISTS 'PONTO_ESTRATEGICO'")
    else:
        # SQLite não tem enum nativo. Aumenta o tamanho declarado para refletir o modelo.
        with op.batch_alter_table('imoveis') as batch:
            batch.alter_column('tipo', existing_type=sa.String(11), type_=sa.String(17), existing_nullable=True)
    op.create_table('boletins_reconhecimento',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('quarteirao_id',sa.Integer(),sa.ForeignKey('quarteiroes.id'),nullable=False,unique=True),
        sa.Column('uf',sa.String(2),nullable=False),
        sa.Column('distrito',sa.String(100),nullable=False),
        sa.Column('municipio',sa.String(100),nullable=False),
        sa.Column('localidade',sa.String(150),nullable=False),
        sa.Column('responsavel',sa.String(150),nullable=False),
        sa.Column('funcao_responsavel',sa.String(30),nullable=False),
        sa.Column('subdistrito',sa.String(100),nullable=True),
        sa.Column('sublocal',sa.String(150),nullable=True),
        sa.Column('categoria',sa.String(50),nullable=False),
        sa.Column('data',sa.Date(),nullable=False),
        sa.Column('created_at',sa.DateTime(),nullable=False),
        sa.Column('updated_at',sa.DateTime(),nullable=False))


def downgrade():
    raise RuntimeError('Esta migração contém boletins e endereços. Restaure uma cópia de segurança para voltar sem perda silenciosa de dados.')
