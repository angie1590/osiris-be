"""insertar tipo de contribuyente

Revision ID: 29d191364ad8
Revises: 4847f320248a
Create Date: 2025-04-22 20:55:10.177163

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29d191364ad8'
down_revision: Union[str, None] = '4847f320248a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    now = datetime.now()
    insert_data = [
        ("01", "Persona Natural", "Persona natural que puede o no llevar contabilidad."),
        ("02", "Sociedad", "Compañía legalmente constituida, obligada a llevar contabilidad."),
        ("03", "RIMPE - Negocio Popular", "Persona natural con ingresos anuales hasta $20,000."),
        ("04", "RIMPE - Emprendedor", "Persona natural o jurídica con ingresos hasta $300,000."),
        ("05", "Gran Contribuyente", "Designado por el SRI por su volumen de actividad."),
    ]

    for codigo, nombre, descripcion in insert_data:
        op.execute(
            sa.text("""
                INSERT INTO aux_tipo_contribuyente (codigo, nombre, descripcion, fecha_creacion, activo)
                VALUES (:codigo, :nombre, :descripcion, :fecha_creacion, :activo)
            """).bindparams(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                fecha_creacion=now,
                activo=True
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    codigos = ['01', '02', '03', '04', '05']
    for codigo in codigos:
        op.execute(
            sa.text("DELETE FROM aux_tipo_contribuyente WHERE codigo = :codigo")
            .bindparams(codigo=codigo)
        )
