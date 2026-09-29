"""Dominio Fundamental da Scientific Systems Exploration Platform (SSEP).

Exportacao dos 15 objetos centrais e tipos fundamentais com invariantes epistemica.
"""

from domain.base import (
    BaseDomainModel,
    SoftLifecycleStatus,
    SemanticVersion,
)
from domain.units import StandardUnit
from domain.epistemic import (
    DataTier,
    EpistemicStatus,
    OperatorType,
    ProvenanceRecord,
    EpistemicRecord,
)
from domain.measurement import (
    UncertaintyType,
    RepresentationType,
    Quantity,
    Measurement,
)
from domain.dataset import Dataset
from domain.source import Source, SourceType, Experiment, Observation
from domain.evidence import EvidenceRecord
from domain.entity import Entity, EntityCategory, EntityType, ExternalIdentifier
from domain.relation import Relation, RelationType
from domain.claim import Claim
from domain.model import (
    ParameterEpistemicOrigin,
    Parameter,
    ModelValidationStatus,
    Model,
)
from domain.simulation import Simulation, Prediction
from domain.hypothesis import Hypothesis
from domain.experiment_design import ExperimentDesign
from domain.conflict import ConflictRecord, ConflictResolutionStatus

__all__ = [
    # Tipos fundamentais
    "BaseDomainModel",
    "SoftLifecycleStatus",
    "SemanticVersion",
    "StandardUnit",
    "DataTier",
    "EpistemicStatus",
    "OperatorType",
    "ProvenanceRecord",
    "EpistemicRecord",
    "UncertaintyType",
    "RepresentationType",
    "Quantity",
    "Measurement",
    "ExternalIdentifier",
    "ParameterEpistemicOrigin",
    "Parameter",
    "ModelValidationStatus",
    "ConflictResolutionStatus",
    # Os 15 Objetos Centrais Normativos
    "Dataset",
    "Source",
    "Experiment",
    "Observation",
    "EvidenceRecord",
    "Entity",
    "Relation",
    "Claim",
    "Model",
    "Parameter",
    "Simulation",
    "Prediction",
    "Hypothesis",
    "ExperimentDesign",
    "ConflictRecord",
]
