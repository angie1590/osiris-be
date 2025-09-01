"""aux: tipo_contribuyente

Revision ID: 70efb3f6be2f
Revises: 0108f5e7731a
Create Date: 2025-09-01 03:28:21.069344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '70efb3f6be2f'
down_revision: Union[str, None] = '0108f5e7731a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "70efb3f6be2f_tipo_contribuyente"
down_revision = "0108f5e7731a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aux_tipo_contribuyente",
        sa.Column("codigo", sa.String(length=8), primary_key=True, nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_aux_tipo_contribuyente_codigo",
        "aux_tipo_contribuyente",
        ["codigo"],
        unique=False,
    )

    # Seed inicial
    rows = [
        {
            "codigo": "01",
            "nombre": "Persona Natural",
            "descripcion": "Persona natural que puede o no llevar contabilidad.",
            "activo": True,
        },
        {
            "codigo": "02",
            "nombre": "Sociedad",
            "descripcion": "Compañía legalmente constituida, obligada a llevar contabilidad.",
            "activo": True,
        },
        {
            "codigo": "03",
            "nombre": "RIMPE - Negocio Popular",
            "descripcion": "Persona natural con ingresos anuales hasta $20,000.",
            "activo": True,
        },
        {
            "codigo": "04",
            "nombre": "RIMPE - Emprendedor",
            "descripcion": "Persona natural o jurídica con ingresos hasta $300,000.",
            "activo": True,
        },
        {
            "codigo": "05",
            "nombre": "Gran Contribuyente",
            "descripcion": "Designado por el SRI por su volumen de actividad.",
            "activo": True,
        },
    ]

    op.bulk_insert(
        sa.table(
            "aux_tipo_contribuyente",
            sa.column("codigo", sa.String),
            sa.column("nombre", sa.String),
            sa.column("descripcion", sa.String),
            sa.column("activo", sa.Boolean),
        ),
        rows,
    )


def downgrade() -> None:
    op.drop_index("ix_aux_tipo_contribuyente_codigo", table_name="aux_tipo_contribuyente")
    op.drop_table("aux_tipo_contribuyente")