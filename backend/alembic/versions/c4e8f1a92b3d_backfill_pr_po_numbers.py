"""backfill_pr_po_numbers

Revision ID: c4e8f1a92b3d
Revises: fef072ebdd1e
Create Date: 2026-07-08 18:56:00.000000

Backfill missing purchase requisition and purchase order numbers for
records created before auto-generation was enforced.
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4e8f1a92b3d"
down_revision: Union[str, Sequence[str], None] = "fef072ebdd1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_pr_counter: int = 0


def _generate_pr_number() -> str:
    global _pr_counter
    _pr_counter += 1
    return f"PR-{datetime.utcnow().strftime('%y%m%d')}-{_pr_counter:05d}"


_po_counter: int = 0


def _generate_po_number() -> str:
    global _po_counter
    _po_counter += 1
    return f"PO-{datetime.utcnow().strftime('%y%m%d')}-{_po_counter:05d}"


def _backfill_numbers(
    conn: sa.Connection,
    *,
    table: str,
    column: str,
    generator,
) -> None:
    rows = conn.execute(
        sa.text(
            f"SELECT id FROM {table} "
            f"WHERE {column} IS NULL OR TRIM({column}) = ''"
        )
    ).fetchall()
    for (record_id,) in rows:
        conn.execute(
            sa.text(f"UPDATE {table} SET {column} = :number WHERE id = :id"),
            {"number": generator(), "id": record_id},
        )


def upgrade() -> None:
    conn = op.get_bind()
    _backfill_numbers(conn, table="purchase_requisitions", column="pr_number", generator=_generate_pr_number)
    _backfill_numbers(conn, table="purchase_orders", column="po_number", generator=_generate_po_number)

    op.alter_column("purchase_requisitions", "pr_number", existing_type=sa.String(length=100), nullable=False)
    op.alter_column("purchase_orders", "po_number", existing_type=sa.String(length=100), nullable=False)


def downgrade() -> None:
    op.alter_column("purchase_orders", "po_number", existing_type=sa.String(length=100), nullable=True)
    op.alter_column("purchase_requisitions", "pr_number", existing_type=sa.String(length=100), nullable=True)
