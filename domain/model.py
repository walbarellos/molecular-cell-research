"""Modelagem de Modelos matematico-computacionais e seus parametros formais."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from domain.base import BaseDomainModel
from domain.units import StandardUnit
from domain.measurement import Quantity


class ParameterEpistemicOrigin(str, Enum):
    MEASURED = "measured"              # Derivado diretamente de evidencia empírica
    ESTIMATED = "estimated"            # Ajustado numericamente ou aproximado
    MODEL_ASSUMPTION = "model_assumption" # Premissa simplificadora sem medicao direta
    UNKNOWN = "unknown"                # Lacuna explicitamente declarada


class Parameter(BaseModel):
    """Variavel quantitativa ou constante requerida por um modelo."""
    model_config = ConfigDict(frozen=True, extra="forbid", use_enum_values=True)

    name: str = Field(..., description="Nome do parametro (ex: k_cat, K_m, step_size, stall_force)")
    description: str = Field(...)
    unit: StandardUnit = Field(...)
    default_value: Optional[float] = Field(default=None)
    origin: ParameterEpistemicOrigin = Field(...)
    evidence_id: Optional[str] = Field(default=None, description="ID da evidencia de suporte quando origin == 'measured'")
    sensitivity_bounds: Optional[List[float]] = Field(default=None, min_length=2, max_length=2)


class ModelValidationStatus(str, Enum):
    UNTESTED = "untested"
    PROVISIONALLY_CONSISTENT = "provisionally_consistent"
    FALSIFIED = "falsified"
    VALIDATED_WITHIN_BOUNDS = "validated_within_bounds"


class Model(BaseDomainModel):
    """Formalismo matematico ou estocastico para reproduzir um fenomeno biofisico."""
    name: str = Field(...)
    description: str = Field(...)
    target_phenomenon: str = Field(..., description="Fenomeno alvo (ex: KIF5B_microtubule_stepping)")
    assumptions: List[str] = Field(..., min_length=1, description="Premissas simplificadoras formalmente declaradas")
    parameters: List[Parameter] = Field(..., min_length=1, description="Lista de parametros requeridos pelo modelo")
    inputs: List[str] = Field(default_factory=list, description="Variaveis de entrada livres (ex: ATP_concentration, load_force)")
    outputs: List[str] = Field(default_factory=list, description="Variaveis geradas pelo modelo (ex: velocity, run_length)")
    equations_or_algorithm_description: str = Field(...)
    implementation_reference: str = Field(..., description="Caminho do script, funcao ou classe executora")
    source_reference: Optional[str] = Field(default=None, description="Paper seminal ou base teorica do modelo")
    validation_status: ModelValidationStatus = Field(default=ModelValidationStatus.UNTESTED)

    @model_validator(mode="after")
    def validate_model_invariants(self) -> "Model":
        # INV-MODEL-001: Um Model deve declarar suas premissas e parametros
        if not self.assumptions:
            raise ValueError("INV-MODEL-001: Model deve declarar ao menos uma premissa explicita em assumptions.")
        if not self.parameters:
            raise ValueError("INV-MODEL-001: Model deve declarar ao menos um parametro formal em parameters.")
        return self
