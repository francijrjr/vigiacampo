"""Converte os valores legados de lado para a numeração da ficha."""
from alembic import op


revision = "c4d05_lado_numerico"
down_revision = "b3e04_antivetorial"
branch_labels = None
depends_on = None


def upgrade():
    # A ficha passou a usar lado 1 e lado 2. Mantém valores já numéricos intactos.
    for tabela in ("imoveis", "quarteiroes"):
        op.execute(
            f"""
            UPDATE {tabela}
            SET lado = CASE lower(trim(lado))
                WHEN 'direito' THEN '1'
                WHEN 'direita' THEN '1'
                WHEN 'esquerdo' THEN '2'
                WHEN 'esquerda' THEN '2'
                ELSE lado
            END
            WHERE lower(trim(lado)) IN ('direito', 'direita', 'esquerdo', 'esquerda')
            """
        )


def downgrade():
    # Não há conversão segura para restaurar o texto de origem.
    pass
