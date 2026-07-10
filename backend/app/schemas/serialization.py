"""
OpenS2P – Safe SQLAlchemy → Pydantic serialization
=====================================================
Avoids the ``MissingGreenlet`` error that occurs when Pydantic's
``model_validate`` tries to read lazy-loaded ORM attributes outside
the async greenlet context.

Usage::

    from app.schemas.serialization import safe_validate

    supplier_data = await safe_validate(SupplierResponse, supplier)
"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


async def safe_validate(
    schema_cls: type[SchemaT],
    model: ModelT | None,
) -> SchemaT | None:
    """Convert a SQLAlchemy model to a Pydantic schema, avoiding greenlet issues.

    Reads column values from ``model.__dict__`` and reads loaded
    relationships via the mapper (without triggering lazy loads).
    """
    if model is None:
        return None

    # 1. Column values — read from __dict__ to avoid greenlet crashes
    data: dict[str, Any] = dict(model.__dict__)
    data.pop("_sa_instance_state", None)

    # 2. Eagerly-loaded relationships — include them so Pydantic can
    #    recursively validate (e.g. WorkflowResponse.tasks).
    mapper = inspect(model)
    for rel in mapper.mapper.relationships:
        if rel.key in model.__dict__:
            data[rel.key] = model.__dict__[rel.key]

    return schema_cls.model_validate(data)
