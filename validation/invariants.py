"""Validadores de Invariantes Epistemica e Integridade Cientifica (INV-001 a INV-007)."""

from typing import List, Optional
from domain.source import Source, Experiment, Observation
from domain.evidence import EvidenceRecord
from domain.claim import Claim
from domain.model import Model
from domain.simulation import Simulation, Prediction
from domain.conflict import ConflictRecord
from domain.epistemic import DataTier, EpistemicStatus


class InvariantViolationError(ValueError):
    """Excecao formal para violacao de integridade epistemica."""
    pass


def verify_inv_evidence_001(evidence: EvidenceRecord) -> None:
    """INV-EVIDENCE-001: Toda Evidence deve possuir origem rastreavel."""
    if not evidence.source_id or not evidence.source_id.strip():
        raise InvariantViolationError("INV-EVIDENCE-001: EvidenceRecord sem source_id valido.")
    if not evidence.experiment_id or not evidence.experiment_id.strip():
        raise InvariantViolationError("INV-EVIDENCE-001: EvidenceRecord sem experiment_id valido.")


def verify_inv_data_001(evidence: EvidenceRecord) -> None:
    """INV-DATA-001: Dados simulados (GENERATED) nao podem ser classificados como experimentais."""
    if evidence.epistemic_record.data_tier == DataTier.GENERATED:
        raise InvariantViolationError("INV-DATA-001: EvidenceRecord contem data_tier GENERATED.")


def verify_inv_claim_001(claim: Claim) -> None:
    """INV-CLAIM-001: Um Claim nao pode ser sustentado sem referencias a evidencias."""
    grounded = (
        EpistemicStatus.OBSERVED,
        EpistemicStatus.REPORTED,
        EpistemicStatus.VALIDATED,
        EpistemicStatus.INFERRED
    )
    if claim.epistemic_record.status in grounded and not claim.supporting_evidence_ids:
        raise InvariantViolationError(
            f"INV-CLAIM-001: Claim '{claim.id}' com status {claim.epistemic_record.status} "
            "exige ao menos uma evidencia em supporting_evidence_ids."
        )


def verify_inv_prediction_001(prediction: Prediction) -> None:
    """INV-PREDICTION-001: Uma Prediction deve indicar qual modelo e simulacao a produziram."""
    if not prediction.model_id or not prediction.model_id.strip():
        raise InvariantViolationError("INV-PREDICTION-001: Prediction sem model_id.")
    if not prediction.simulation_id or not prediction.simulation_id.strip():
        raise InvariantViolationError("INV-PREDICTION-001: Prediction sem simulation_id.")


def verify_inv_model_001(model: Model) -> None:
    """INV-MODEL-001: Um Model deve declarar suas premissas e parametros."""
    if not model.assumptions:
        raise InvariantViolationError(f"INV-MODEL-001: Model '{model.id}' nao possui premissas declaradas.")
    if not model.parameters:
        raise InvariantViolationError(f"INV-MODEL-001: Model '{model.id}' nao possui parametros declarados.")


def verify_inv_repro_001(simulation: Simulation) -> None:
    """INV-REPRO-001: Uma execucao deve registrar versoes e hash de execucao."""
    if not simulation.model_version:
        raise InvariantViolationError("INV-REPRO-001: Simulation sem model_version.")
    if not simulation.execution_hash:
        raise InvariantViolationError("INV-REPRO-001: Simulation sem execution_hash.")


def verify_chain_referential_integrity(
    source: Source,
    experiment: Experiment,
    observation: Observation,
    evidence: EvidenceRecord,
    claim: Claim,
    model: Model,
    simulation: Simulation,
    prediction: Prediction
) -> None:
    """Verifica a cadeia epistemica completa de ponta a ponta sem quebra de referencias."""
    if experiment.source_id != source.id:
        raise InvariantViolationError(f"Cadeia quebrada: Experiment '{experiment.id}' aponta para source_id '{experiment.source_id}', mas Source.id e '{source.id}'.")
    
    if observation.experiment_id != experiment.id:
        raise InvariantViolationError(f"Cadeia quebrada: Observation '{observation.id}' nao pertence a Experiment '{experiment.id}'.")

    if evidence.source_id != source.id:
        raise InvariantViolationError(f"Cadeia quebrada: Evidence '{evidence.id}' referencia source_id incorreto.")

    if evidence.experiment_id != experiment.id:
        raise InvariantViolationError(f"Cadeia quebrada: Evidence '{evidence.id}' referencia experiment_id incorreto.")

    if observation.id not in evidence.observation_ids:
        raise InvariantViolationError(f"Cadeia quebrada: Observation '{observation.id}' nao consta nos observation_ids de Evidence '{evidence.id}'.")

    if evidence.id not in claim.supporting_evidence_ids:
        raise InvariantViolationError(f"Cadeia quebrada: Evidence '{evidence.id}' nao consta em supporting_evidence_ids de Claim '{claim.id}'.")

    if simulation.model_id != model.id:
        raise InvariantViolationError(f"Cadeia quebrada: Simulation '{simulation.id}' referencia model_id incorreto.")

    if prediction.model_id != model.id:
        raise InvariantViolationError(f"Cadeia quebrada: Prediction '{prediction.id}' referencia model_id incorreto.")

    if prediction.simulation_id != simulation.id:
        raise InvariantViolationError(f"Cadeia quebrada: Prediction '{prediction.id}' referencia simulation_id incorreto.")
