"""
Shared Pydantic schema base classes.

`ORMBase` is used by every "read" schema that's built from a SQLAlchemy
model instance (enables `model_validate(orm_obj)` via `from_attributes`).
"""

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    """Base class for schemas that are constructed from ORM model instances."""

    model_config = ConfigDict(from_attributes=True)
