"""Modelagem de Entidades biologicas, fisicas e conceituais do dominio."""

from enum import Enum
from typing import Any, Dict, List
from pydantic import Field
from domain.base import BaseDomainModel


class EntityCategory(str, Enum):
    BIOLOGICAL = "biological"
    PHYSICAL = "physical"
    CONCEPTUAL = "conceptual"


class EntityType(str, Enum):
    # Biologicas
    PROTEIN = "protein"
    MOLECULE = "molecule"
    COMPLEX = "complex"
    STRUCTURE = "structure"

    # Fisicas
    FILAMENT = "filament"
    COMPARTMENT = "compartment"

    # Conceituais
    PROCESS = "process"
    STATE = "state"


class ExternalIdentifier(BaseDomainModel):
    database_name: str = Field(..., description="UniProt, PDB, ChEMBL, NCBI, GO, etc.")
    accession_code: str = Field(...)


class Entity(BaseDomainModel):
    """Objeto biologico, fisico ou conceitual com identidade persistente."""
    category: EntityCategory = Field(...)
    entity_type: EntityType = Field(...)
    canonical_name: str = Field(..., description="Nome cientifico padronizado (ex: KIF5B, Microtubule, ATP)")
    systematic_name: str = Field(..., description="Identificador sistematico ou sinonimo primario")
    external_identifiers: List[ExternalIdentifier] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Propriedades intrinsecas estaveis (ex: massa molecular, sequencia)")
