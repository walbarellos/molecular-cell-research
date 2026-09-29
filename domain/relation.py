"""Modelagem de Relacoes estruturais e funcionais entre entidades biologicas."""

from enum import Enum
from typing import Any, Dict, List
from pydantic import Field
from domain.base import BaseDomainModel


class RelationType(str, Enum):
    BINDS_TO = "binds_to"
    TRANSLOCATES_ALONG = "translocates_along"
    HYDROLYZES = "hydrolyzes"
    INHIBITS = "inhibits"
    STABILIZES = "stabilizes"
    CARRIES = "carries"
    TRANSITIONS_TO = "transitions_to"
    PART_OF = "part_of"


class Relation(BaseDomainModel):
    """Vinculo formal orientado entre duas entidades no grafo de conhecimento."""
    source_entity_id: str = Field(..., description="ID da entidade de origem (sujeito)")
    target_entity_id: str = Field(..., description="ID da entidade de destino (objeto)")
    relation_type: RelationType = Field(...)
    bidirectional: bool = Field(default=False)
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs de EvidenceRecords que sustentam esta relacao")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Constantes cineticas ou propriedades especificas do vinculo")
