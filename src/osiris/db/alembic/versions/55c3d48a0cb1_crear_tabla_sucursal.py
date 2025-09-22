"""crear tabla sucursal

Revision ID: 55c3d48a0cb1
Revises: e2bef79425b7
Create Date: 2025-09-02 03:05:13.937506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "55c3d48a0cb1"
down_revision: Union[str, None] = "e2bef79425b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tbl_sucursal",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("codigo", sa.String(length=3), nullable=False),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.Column("direccion", sa.String(length=100), nullable=False),
        sa.Column("telefono", sa.String(length=15), nullable=True),

        # SoftDeleteMixin
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),

        # AuditMixin
        sa.Column("creado_en", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("usuario_auditoria", sa.String(length=255), nullable=True),

        # FK
        sa.Column("empresa_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["tbl_empresa.id"]),

        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tbl_sucursal_id"), "tbl_sucursal", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_tbl_sucursal_id"), table_name="tbl_sucursal")
    op.drop_table("tbl_sucursal")
