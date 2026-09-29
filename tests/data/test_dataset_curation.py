"""Testes de integridade, proveniencia e controle de qualidade dos Datasets Curados (Ciclo 04)."""

import hashlib
import json
from pathlib import Path
import pytest

from domain import (
    Dataset,
    Source,
    Experiment,
    Observation,
    EvidenceRecord,
    DataTier,
    EpistemicStatus,
    StandardUnit,
)
from validation import verify_inv_evidence_001, verify_inv_data_001


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_dataset_a_calibration_integrity():
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_csv = project_root / "data" / "raw" / "cell_lab_001" / "schnitzer_block_1997_unloaded_velocity.csv"
    derived_json = project_root / "data" / "derived" / "cell_lab_001" / "dataset_a_calibration.json"

    assert raw_csv.exists(), "Arquivo bruto de Dataset A deve existir."
    assert derived_json.exists(), "Arquivo derivado normalizado de Dataset A deve existir."

    raw_sha = compute_sha256(raw_csv)

    with open(derived_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    dataset = Dataset.model_validate(payload["dataset"])
    source = Source.model_validate(payload["source"])
    experiment = Experiment.model_validate(payload["experiment"])
    observations = [Observation.model_validate(o) for o in payload["observations"]]
    evidences = [EvidenceRecord.model_validate(e) for e in payload["evidences"]]

    # Validacao de hash e tier
    assert dataset.checksum_sha256 == raw_sha
    assert dataset.data_tier == DataTier.RAW
    assert dataset.record_count == 10
    assert len(observations) == 10
    assert len(evidences) == 10

    # Invariantes nos registros de evidencia
    for evi in evidences:
        verify_inv_evidence_001(evi)
        verify_inv_data_001(evi)
        assert evi.source_id == source.id
        assert evi.experiment_id == experiment.id
        assert evi.conditions["load_force_pN"] == 0.0
        assert evi.conditions["atp_concentration_uM"] > 0

    # Validacao quantitativa das observacoes
    for obs in observations:
        mea = obs.measurements[0]
        assert mea.measured_property == "velocity"
        assert mea.quantity.unit == StandardUnit.MICROMETER_PER_SECOND
        assert mea.quantity.value > 0.0
        assert mea.quantity.uncertainty is not None
        assert mea.quantity.uncertainty > 0.0


def test_dataset_b_falsification_integrity():
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_csv = project_root / "data" / "raw" / "cell_lab_001" / "visscher_block_1999_force_velocity.csv"
    derived_json = project_root / "data" / "derived" / "cell_lab_001" / "dataset_b_falsification.json"

    assert raw_csv.exists(), "Arquivo bruto de Dataset B deve existir."
    assert derived_json.exists(), "Arquivo derivado normalizado de Dataset B deve existir."

    raw_sha = compute_sha256(raw_csv)

    with open(derived_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    dataset = Dataset.model_validate(payload["dataset"])
    source = Source.model_validate(payload["source"])
    experiment = Experiment.model_validate(payload["experiment"])
    observations = [Observation.model_validate(o) for o in payload["observations"]]
    evidences = [EvidenceRecord.model_validate(e) for e in payload["evidences"]]

    # Validacao de hash e tier
    assert dataset.checksum_sha256 == raw_sha
    assert dataset.data_tier == DataTier.RAW
    assert dataset.record_count == 11
    assert len(observations) == 11
    assert len(evidences) == 11

    # Invariantes nos registros de evidencia
    for evi in evidences:
        verify_inv_evidence_001(evi)
        verify_inv_data_001(evi)
        assert evi.source_id == source.id
        assert evi.experiment_id == experiment.id
        assert evi.conditions["load_force_pN"] >= 0.0
        assert evi.conditions["atp_concentration_uM"] in (10.0, 1000.0)

    # Validacao de forcas contrarias
    loads = [obs.measurements[0].conditions["load_force_pN"] for obs in observations]
    assert max(loads) == 6.0
    assert min(loads) == 0.0


def test_manifest_consistency():
    project_root = Path(__file__).resolve().parent.parent.parent
    manifest_path = project_root / "data" / "derived" / "cell_lab_001" / "manifest_cell_lab_001.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phenomenon"] == "CELL-LAB-001"
    assert "calibration_dataset_a" in manifest["datasets"]
    assert "falsification_dataset_b" in manifest["datasets"]
    assert manifest["datasets"]["calibration_dataset_a"]["record_count"] == 10
    assert manifest["datasets"]["falsification_dataset_b"]["record_count"] == 11
