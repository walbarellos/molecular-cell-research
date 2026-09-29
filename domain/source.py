"""Modelagem de Fontes cientificas, Experimentos documentados e Observacoes primarias."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import ConfigDict, Field
from domain.base import BaseDomainModel
from domain.measurement import Measurement


class SourceType(str, Enum):
    JOURNAL_ARTICLE = "journal_article"
    DATABASE_ENTRY = "database_entry"
    PREPRINT = "preprint"
    TECHNICAL_REPORT = "technical_report"
    DATASET_REPOSITORY = "dataset_repository"


class Source(BaseDomainModel):
    """Artigo cientifico, entrada de banco de dados publico ou relatorio de origem."""
    source_type: SourceType = Field(...)
    identifier: str = Field(..., description="DOI, PubMed ID, UniProt ID, PDB ID ou URI estavel")
    title: str = Field(...)
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = Field(default=None)
    publication_venue: Optional[str] = Field(default=None, description="Nome do periodico ou base de dados")
    uri: Optional[str] = Field(default=None)
    content_hash_sha256: Optional[str] = Field(default=None, description="Hash SHA-256 do arquivo ou documento bruto de origem")


class Experiment(BaseDomainModel):
    """Ensaio fisico ou protocolo analitico documentado em uma Source."""
    source_id: str = Field(..., description="ID da Source documentada que descreve o ensaio")
    name: str = Field(..., description="Denominacao do ensaio ou ensaio comparativo")
    method: str = Field(..., description="Metodologia ou tecnica (ex: optical_tweezers, TIRF_microscopy)")
    protocol_description: Optional[str] = Field(default=None)
    environmental_conditions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Temperatura, tampao, pH, ATP inicial, forca ionica, etc."
    )


class Observation(BaseDomainModel):
    """Leitura quantitativa ou qualitativa direta extraida de um Experiment."""
    experiment_id: str = Field(..., description="ID do experimento do qual a observacao se originou")
    description: str = Field(..., description="Descricao objetiva do fenomeno ou medicao observada")
    measurements: List[Measurement] = Field(default_factory=list, description="Conjunto de medicoes associadas a esta observacao")
    raw_data_ref: Optional[str] = Field(default=None, description="Referencia a arquivo de dados bruto em L2")
