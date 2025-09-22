"""crear tabla punto emision

Revision ID: 154699fe5d08
Revises: 55c3d48a0cb1
Create Date: 2025-09-02 03:40:40.623188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "154699fe5d08"
down_revision: Union[str, None] = "55c3d48a0cb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tbl_punto_emision",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("codigo", sa.String(length=3), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=False),
        sa.Column("secuencial_actual", sa.Integer(), nullable=False),

        # SoftDeleteMixin
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),

        # AuditMixin
        sa.Column("creado_en", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("actualizado_en", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("usuario_auditoria", sa.String(length=255), nullable=False),

        # FKs
        sa.Column("empresa_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("sucursal_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["empresa_id"], ["tbl_empresa.id"]),
        sa.ForeignKeyConstraint(["sucursal_id"], ["tbl_sucursal.id"]),

        sa.UniqueConstraint("codigo", "empresa_id", "sucursal_id", name="uq_codigo_por_entidad"),
    )
    op.create_index(op.f("ix_tbl_punto_emision_id"), "tbl_punto_emision", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_tbl_punto_emision_id"), table_name="tbl_punto_emision")
    op.drop_table("tbl_punto_emision")
