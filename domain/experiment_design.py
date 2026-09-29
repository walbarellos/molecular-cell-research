"""Modelagem de Desenho Experimental Discriminatorio (L6)."""

from typing import Any, Dict, List, Optional
from pydantic import Field
from domain.base import BaseDomainModel


class ExperimentDesign(BaseDomainModel):
    """Proposta de ensaio empirico ou virtual projetada especificamente para diferenciar modelos ou reduzir incerteza."""
    title: str = Field(...)
    objective: str = Field(..., description="Pergunta cientifica ou diferenciacao pretendida")
    competing_model_ids: List[str] = Field(..., min_length=1, description="Modelos que preveem comportamentos distintos neste ensaio")
    target_conditions: Dict[str, Any] = Field(..., description="Variaveis sob teste (ex: ATP < 5 uM sob forca contraria de 4 pN)")
    proposed_technique: str = Field(..., description="Metodo experimental sugerido (ex: high-speed optical tweezers)")
    predicted_outcomes: Dict[str, str] = Field(
        ...,
        description="Mapeamento de model_id -> comportamento esperado segundo o modelo"
    )
    discriminatory_power_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Indice quantitativo do poder de resolucao entre as hipoteses"
    )
