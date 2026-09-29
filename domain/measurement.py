"""Modelagem formal de grandezas fisicas, incertezas e medicoes quantitativas."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from domain.base import BaseDomainModel
from domain.units import StandardUnit


class UncertaintyType(str, Enum):
    NONE = "none"
    STANDARD_ERROR = "standard_error"
    STANDARD_DEVIATION = "standard_deviation"
    CONFIDENCE_INTERVAL_95 = "confidence_interval_95"
    RANGE = "range"
    SYSTEMATIC_ERROR = "systematic_error"


class RepresentationType(str, Enum):
    POINT_ESTIMATE = "point_estimate"
    DISTRIBUTION = "distribution"
    INTERVAL = "interval"
    BOUNDS = "bounds"


class Quantity(BaseModel):
    """Representacao de grandeza fisica quantitativa com unidade e incerteza obrigatorias."""
    model_config = ConfigDict(frozen=True, extra="forbid", use_enum_values=True)

    value: float = Field(..., description="Valor numerico central medido ou computado")
    unit: StandardUnit = Field(..., description="Unidade fisica estrita")
    uncertainty: Optional[float] = Field(default=None, ge=0.0, description="Margem de incerteza associada")
    uncertainty_type: UncertaintyType = Field(default=UncertaintyType.NONE)
    representation: RepresentationType = Field(default=RepresentationType.POINT_ESTIMATE)

    @model_validator(mode="after")
    def validate_uncertainty_pairing(self) -> "Quantity":
        if self.uncertainty is not None and self.uncertainty_type == UncertaintyType.NONE:
            raise ValueError("Valor de incerteza fornecido exige definicao de uncertainty_type diferente de 'none'.")
        if self.uncertainty is None and self.uncertainty_type != UncertaintyType.NONE:
            raise ValueError(f"uncertainty_type '{self.uncertainty_type}' fornecido sem valor de incerteza numerico.")
        return self


class Measurement(BaseDomainModel):
    """Medicao contextualizada ligada a uma propriedade especifica de uma entidade."""
    quantity: Quantity = Field(..., description="Grandeza quantitativa aferida")
    measured_property: str = Field(..., description="Nome padronizado da propriedade (ex: velocity, stall_force, run_length)")
    entity_id: str = Field(..., description="Identificador da entidade a que se refere a medicao")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Condicoes experimentais na realizacao da medicao")
    method: str = Field(..., description="Metodo experimental ou analitico utilizado")
    observation_id: Optional[str] = Field(default=None, description="Identificador da observacao que documenta esta medicao")
