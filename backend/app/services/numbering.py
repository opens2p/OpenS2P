"""
OpenS2P – Sequential Document Numbering
=========================================
Generates human-readable sequential document numbers for purchase
requisitions and purchase orders in the format::

    {PREFIX}-{YYMMDD}-{XXXXX}

Examples::

    PR-260710-00001
    PO-260710-00001
    PO-260710-00002

The sequential counter resets monthly (based on the YYMM portion).
Numbers within the same month share a continuous sequence, so a
PR created on the 10th will have a higher number than one created
on the 5th, and the counter restarts at 00001 each month.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def _yyymm() -> str:
    """Return the current year-month as a 4-character *YYMM* string
    used for monthly counter reset grouping."""
    return datetime.utcnow().strftime("%y%m")


def _yymmdd() -> str:
    """Return today's date as a 6-character *YYMMDD* string
    used for the display prefix in the document number."""
    return datetime.utcnow().strftime("%y%m%d")


def _parse_sequence(document_number: str) -> int:
    """Extract the 5-digit sequential portion from a document number."""
    return int(document_number.rsplit("-", 1)[-1])


def derive_po_number(pr_number: str) -> str:
    """Derive a matching PO number from a PR number.

    If the PR number is ``PR-260710-00001`` the returned PO number
    will be ``PO-260710-00001`` — same date and sequential portion,
    different document prefix.
    """
    return pr_number.replace("PR-", "PO-", 1)


async def next_document_number(
    session: AsyncSession,
    model,
    column: str,
    prefix: str,
) -> str:
    """Generate the next sequential document number for *prefix*.

    Parameters
    ----------
    session :
        Active database session.
    model :
        SQLAlchemy model class (e.g. ``PurchaseRequisition``).
    column :
        Name of the column that stores the document number
        (e.g. ``"pr_number"`` or ``"po_number"``).
    prefix :
        Two-letter document prefix (``"PR"`` or ``"PO"``).

    Returns
    -------
    str
        Formatted number, e.g. ``PR-260710-00001``.

    Notes
    -----
    The sequential counter resets monthly. The query uses a *YYMM*
    prefix pattern (``PR-2607-%``) so all documents from the same
    month contribute to one running sequence, regardless of the day.

    The column must have a ``UNIQUE`` constraint so that any
    concurrent collision raises an integrity error rather than
    producing duplicates.
    """
    month = _yyymm()       # e.g. "2607" — for grouping
    today = _yymmdd()      # e.g. "260710" — for display

    # Query using YYMonth pattern so the counter spans the whole month.
    # Use "{prefix}-{month}%" (no trailing dash after month) because
    # the actual number has YYMMDD after the prefix, e.g. PR-260710-00001.
    # The dash after the month would never match since day digits follow.
    pattern = f"{prefix}-{month}%"
    column_attr = getattr(model, column)
    stmt = select(func.max(column_attr)).where(column_attr.like(pattern))
    result = await session.execute(stmt)
    max_number: str | None = result.scalar()

    if max_number:
        next_seq = _parse_sequence(max_number) + 1
    else:
        next_seq = 1

    return f"{prefix}-{today}-{next_seq:05d}"
