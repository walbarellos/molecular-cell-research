"""Modelagem formal de Afirmacoes cientificas (Claims) e integridade referencial."""

from typing import List, Optional
from pydantic import Field, model_validator
from domain.base import BaseDomainModel
from domain.epistemic import EpistemicRecord, EpistemicStatus


class Claim(BaseDomainModel):
    """Proposicao declarativa a respeito do comportamento, funcao ou estado de uma entidade."""
    statement: str = Field(..., description="Texto claro e auditavel da afirmacao cientifica")
    subject_entity_id: str = Field(..., description="ID da entidade biológica/física que atua como sujeito")
    predicate: str = Field(..., description="Verbo ou relacao formalizada (ex: exhibits_unidirectional_motion_on)")
    object_entity_id: Optional[str] = Field(default=None, description="ID da entidade alvo, se aplicavel")
    epistemic_record: EpistemicRecord = Field(..., description="Envelope epistemico da afirmacao")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Lista de IDs de EvidenceRecords que sustentam a Claim")
    conflicting_evidence_ids: List[str] = Field(default_factory=list, description="Lista de IDs de EvidenceRecords que divergem ou contradizem a Claim")

    @model_validator(mode="after")
    def validate_claim_invariants(self) -> "Claim":
        # INV-CLAIM-001: Afirmacao com status validado, observado ou inferido exige suporte documental
        grounded_statuses = (
            EpistemicStatus.OBSERVED,
            EpistemicStatus.REPORTED,
            EpistemicStatus.VALIDATED,
            EpistemicStatus.INFERRED
        )
        if self.epistemic_record.status in grounded_statuses:
            if not self.supporting_evidence_ids:
                raise ValueError(
                    f"INV-CLAIM-001: Claim com status epistemico '{self.epistemic_record.status}' "
                    "deve possuir ao menos uma evidencia em supporting_evidence_ids."
                )
        return self
