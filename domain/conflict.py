"""Modelagem de Registro de Conflitos e Contradicoes epistemica."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import Field
from domain.base import BaseDomainModel


class ConflictResolutionStatus(str, Enum):
    UNRESOLVED = "unresolved"
    EXPLAINED_BY_CONDITIONS = "explained_by_conditions"
    ONE_SUPERSEDED = "one_superseded"
    METHODOLOGICAL_ARTIFACT = "methodological_artifact"
    TRUE_CONTRADICTION = "true_contradiction"


class ConflictRecord(BaseDomainModel):
    """Registro de divergencia ou incompatibilidade entre afirmacoes, evidencias ou modelos."""
    claim_a_id: Optional[str] = Field(default=None)
    claim_b_id: Optional[str] = Field(default=None)
    evidence_a_id: str = Field(..., description="ID da primeira evidencia divergente")
    evidence_b_id: str = Field(..., description="ID da segunda evidencia divergente")
    divergence_metric: str = Field(..., description="Descricao ou metrica quantitativa da divergencia (ex: velocidade 2x maior)")
    conditions_comparison: Dict[str, Any] = Field(
        default_factory=dict,
        description="Comparativo de condicoes fisico-quimicas (temperatura, pH, mutacao) que podem explicar a discrepancia"
    )
    resolution_status: ConflictResolutionStatus = Field(default=ConflictResolutionStatus.UNRESOLVED)
    resolution_notes: Optional[str] = Field(default=None)
