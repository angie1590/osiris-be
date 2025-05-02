"""agrega enum tipo_identificacion

Revision ID: cbcc9b497454
Revises: 464d64766238
Create Date: 2025-05-02 15:33:47.647426
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbcc9b497454'
down_revision: Union[str, None] = '464d64766238'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        CREATE TYPE tipo_identificacion_enum AS ENUM ('CEDULA', 'RUC', 'PASAPORTE')
    """)

    op.add_column('tbl_persona', sa.Column('identificacion', sa.String(), nullable=False))

    op.execute("""
        ALTER TABLE tbl_persona
        ALTER COLUMN tipo_identificacion
        TYPE tipo_identificacion_enum
        USING tipo_identificacion::tipo_identificacion_enum
    """)

    op.create_unique_constraint(None, 'tbl_persona', ['identificacion'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'tbl_persona', type_='unique')
    op.alter_column(
        'tbl_persona',
        'tipo_identificacion',
        existing_type=sa.Enum('CEDULA', 'RUC', 'PASAPORTE', name='tipo_identificacion_enum'),
        type_=sa.VARCHAR(),
        existing_nullable=False
    )
    op.drop_column('tbl_persona', 'identificacion')
    op.execute("DROP TYPE tipo_identificacion_enum")