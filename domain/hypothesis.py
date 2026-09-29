"""Modelagem de Hipoteses cientificas sujeitas a falsificacao."""

from typing import List
from pydantic import Field
from domain.base import BaseDomainModel
from domain.epistemic import EpistemicRecord


class Hypothesis(BaseDomainModel):
    """Estrutura explicativa candidata formulada para explicar lacunas ou divergencias."""
    statement: str = Field(..., description="Proposicao teorica a ser testada")
    rationale: str = Field(..., description="Justificativa logica ou mecanistica de base")
    competing_model_ids: List[str] = Field(default_factory=list, description="Modelos alternativos que competem com esta hipotese")
    falsification_criteria: List[str] = Field(..., min_length=1, description="Condicoes objetivas sob as quais a hipotese e considerada refutada")
    epistemic_record: EpistemicRecord = Field(...)
