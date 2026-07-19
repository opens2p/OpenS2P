"""add_receipt_qty_fields

Revision ID: a7c3e9f12d45
Revises: 1e1f8ecd249c
Create Date: 2026-07-18 10:40:00.000000

Add quantity_received and amount_received to receipts for 3-way match.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7c3e9f12d45"
down_revision: Union[str, Sequence[str], None] = "1e1f8ecd249c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "receipts",
        sa.Column("quantity_received", sa.Numeric(15, 2), nullable=True),
    )
    op.add_column(
        "receipts",
        sa.Column("amount_received", sa.Numeric(15, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("receipts", "amount_received")
    op.drop_column("receipts", "quantity_received")
