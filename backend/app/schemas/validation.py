"""Schemas for Policy / Validation Agent – booking and passenger validation."""

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Output of Policy/Validation Agent."""

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
