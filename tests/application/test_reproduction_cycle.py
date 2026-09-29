"""Testes automatizados do Ciclo 06: Bateria de Reproducao Computacional sobre Dataset A."""

import json
from pathlib import Path
import pytest

from application.run_reproduction_cycle import execute_dataset_a_reproduction
from domain import Claim, EpistemicStatus
from validation import verify_inv_claim_001


def test_reproduction_cycle_dataset_a():
    output_report = execute_dataset_a_reproduction()

    assert output_report["reproduction_phenomenon"] == "CELL-LAB-001"
    assert output_report["dataset_evaluated"] == "DTS-CELL-LAB-001-CALIBRATION"

    comparison = output_report["comparison"]
    assert comparison["verdict"] == "REPRODUCED_CONSISTENT"

    metrics = comparison["metrics"]
    assert metrics["sample_count"] == 10
    assert metrics["within_2_sigma_count"] == 10
    assert metrics["within_2_sigma_ratio"] == 1.0
    assert metrics["r_squared"] > 0.99
    assert metrics["chi2_reduced"] < 1.5
    assert metrics["rmse"] < 0.03  # RMSE menor que 0.03 um/s

    # Valida o Claim gerado
    claim_data = output_report["validation_claim"]
    claim = Claim.model_validate(claim_data)
    verify_inv_claim_001(claim)

    assert claim.epistemic_record.status == EpistemicStatus.VALIDATED
    assert len(claim.supporting_evidence_ids) == 10
    assert len(claim.conflicting_evidence_ids) == 0


def test_reproduction_report_file_integrity():
    project_root = Path(__file__).resolve().parent.parent.parent
    report_file = project_root / "data" / "derived" / "cell_lab_001" / "reproduction_report_dataset_a.json"

    assert report_file.exists(), "Relatorio em disco deve existir."

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["comparison"]["verdict"] == "REPRODUCED_CONSISTENT"
    assert len(data["comparison"]["point_comparisons"]) == 10
