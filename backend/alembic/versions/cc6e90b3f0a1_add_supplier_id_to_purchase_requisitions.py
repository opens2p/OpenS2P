"""add_supplier_id_to_purchase_requisitions

Revision ID: cc6e90b3f0a1
Revises: c4e8f1a92b3d
Create Date: 2026-07-09 10:00:00.000000

Add supplier_id FK column to purchase_requisitions so that a
supplier can be associated with a PR and flow through to the PO
when the PR is approved.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "cc6e90b3f0a1"
down_revision: Union[str, Sequence[str], None] = "c4e8f1a92b3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "purchase_requisitions",
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("purchase_requisitions", "supplier_id")
