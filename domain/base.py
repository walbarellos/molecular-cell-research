"""Nucleo de tipos fundamentais e metadados base para integridade epistemica."""

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional
import uuid
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SoftLifecycleStatus(str, Enum):
    """Ciclo de vida do registro cientifico (sem delecao destrutiva)."""
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"
    INVALIDATED = "invalidated"
    RETRACTED = "retracted"


class SemanticVersion(BaseModel):
    """Representacao de versao semantica (MAJOR.MINOR.PATCH)."""
    model_config = ConfigDict(frozen=True)

    version_str: str = Field(..., pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")

    @classmethod
    def from_string(cls, v: str) -> "SemanticVersion":
        return cls(version_str=v)

    def __str__(self) -> str:
        return self.version_str


class BaseDomainModel(BaseModel):
    """Modelo base para todas as entidades e registros do sistema."""
    model_config = ConfigDict(
        frozen=False,
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True
    )

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lifecycle_status: SoftLifecycleStatus = Field(default=SoftLifecycleStatus.ACTIVE)
    version: str = Field(default="1.0.0")

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
        if not re.match(pattern, v):
            raise ValueError(f"Versao semantica invalida: {v}. Esperado formato MAJOR.MINOR.PATCH")
        return v
