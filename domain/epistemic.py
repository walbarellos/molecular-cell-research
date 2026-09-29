"""Modelo epistemologico, classificacao de tiers de dados e integridade cientifica."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class DataTier(str, Enum):
    """Classificacao estrita da camada de dados."""
    RAW = "RAW"              # Dados brutos experimentais, imutaveis, de fontes externas
    DERIVED = "DERIVED"      # Dados agregados, normalizados, calculados a partir de RAW
    GENERATED = "GENERATED"  # Saidas computacionais, simuladas ou sinteticas


class EpistemicStatus(str, Enum):
    """Estados da maquina de estados de integridade epistemica."""
    UNKNOWN = "UNKNOWN"
    OBSERVED = "OBSERVED"
    REPORTED = "REPORTED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    HYPOTHESIS = "HYPOTHESIS"
    MODELED = "MODELED"
    PREDICTED = "PREDICTED"
    VALIDATED = "VALIDATED"
    CONTRADICTED = "CONTRADICTED"


class OperatorType(str, Enum):
    HUMAN = "HUMAN"
    SCRIPT = "SCRIPT"
    PIPELINE = "PIPELINE"
    MODEL = "MODEL"


class ProvenanceRecord(BaseModel):
    """Rastreabilidade de origem de uma afirmacao ou medicao."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_uri: str = Field(..., description="URI, DOI ou identificador persistente da fonte")
    method: str = Field(..., description="Tecnica experimental, algoritmo ou protocolo empregado")
    operator: OperatorType = Field(default=OperatorType.HUMAN)
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Parametros de contorno da medicao")


class EpistemicRecord(BaseModel):
    """Envelope transversal que carrega status epistemico, tier e condicoes."""
    model_config = ConfigDict(frozen=True, extra="forbid", use_enum_values=True)

    status: EpistemicStatus = Field(...)
    data_tier: DataTier = Field(...)
    provenance: Optional[ProvenanceRecord] = Field(default=None)
    basis: List[str] = Field(default_factory=list, description="IDs de observacoes ou evidencias que sustentam este registro")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Condicoes fisico-quimicas especificas sob as quais este status e valido")
    limitations: List[str] = Field(default_factory=list, description="Limites explicitos de validade ou advertencias metodologicas")
    confidence_evidence_count: int = Field(default=0, ge=0, description="Numero de evidencias independentes que suportam a proposicao")

    @model_validator(mode="after")
    def validate_epistemic_integrity(self) -> "EpistemicRecord":
        # Invariante: Dados RAW nao podem ser resultado de modelagem ou predicao
        if self.data_tier == DataTier.RAW:
            if self.status in (EpistemicStatus.MODELED, EpistemicStatus.PREDICTED, EpistemicStatus.HYPOTHESIS):
                raise ValueError(
                    f"Violacao de integridade: data_tier RAW nao pode possuir status {self.status}"
                )
        # Invariante: Dados GENERATED nao podem ser classificados como OBSERVED diretamente
        if self.data_tier == DataTier.GENERATED:
            if self.status in (EpistemicStatus.OBSERVED, EpistemicStatus.REPORTED):
                raise ValueError(
                    f"Violacao de integridade: data_tier GENERATED nao pode ser rotulado como {self.status}"
                )
        return self
