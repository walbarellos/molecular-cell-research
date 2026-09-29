"""Modelagem de Evidencias cientificas auditadas e proveniencia estrita."""

from typing import Any, Dict, List
from pydantic import Field, model_validator
from domain.base import BaseDomainModel
from domain.epistemic import EpistemicRecord, EpistemicStatus, DataTier


class EvidenceRecord(BaseDomainModel):
    """Evidencia experimental curada e contextualizada metodologicamente."""
    source_id: str = Field(..., description="ID da Source bibliografica ou base primaria")
    experiment_id: str = Field(..., description="ID do ensaio experimental especifico de onde a evidencia foi extraida")
    observation_ids: List[str] = Field(default_factory=list, description="IDs das Observacoes que fornecem a base empírica")
    supports_claims: List[str] = Field(default_factory=list, description="IDs de Claims sustentadas por esta evidencia")
    contradicts_claims: List[str] = Field(default_factory=list, description="IDs de Claims refutadas ou conflitadas por esta evidencia")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Condicoes de contorno do ensaio (temperatura, pH, forca ionica, etc.)")
    epistemic_record: EpistemicRecord = Field(..., description="Envelope epistemico associado a evidencia")

    @model_validator(mode="after")
    def validate_evidence_invariants(self) -> "EvidenceRecord":
        # INV-EVIDENCE-001: Toda Evidence deve possuir origem rastreavel (source_id e experiment_id nao vazios)
        if not self.source_id or not self.source_id.strip():
            raise ValueError("INV-EVIDENCE-001: EvidenceRecord exige source_id valido.")
        if not self.experiment_id or not self.experiment_id.strip():
            raise ValueError("INV-EVIDENCE-001: EvidenceRecord exige experiment_id valido.")
        
        # Invariante: Evidencia empirica deve pertencer a tier RAW ou DERIVED, nunca GENERATED diretamente
        if self.epistemic_record.data_tier == DataTier.GENERATED:
            raise ValueError("INV-DATA-001: EvidenceRecord nao pode ser instanciado com data_tier GENERATED.")
        return self
