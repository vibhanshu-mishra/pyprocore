"""Base model primitives for Procore response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProcoreModel(BaseModel):
    """Base model that preserves unknown Procore response fields."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)
