"""fixing empleado activo type

Revision ID: 0eb25a2376f7
Revises: cbcc9b497454
Create Date: 2025-05-02 17:49:35.179230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0eb25a2376f7'
down_revision: Union[str, None] = 'cbcc9b497454'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Cast explícito si ya existen datos compatibles
    op.execute("""
        ALTER TABLE tbl_empleado
        ALTER COLUMN activo
        TYPE boolean
        USING (activo::boolean)
    """)

def downgrade():
    op.execute("""
        ALTER TABLE tbl_empleado
        ALTER COLUMN activo
        TYPE varchar
        USING (activo::varchar)
    """)