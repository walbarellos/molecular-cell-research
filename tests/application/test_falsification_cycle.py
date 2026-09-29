"""Testes automatizados do Ciclo 07: Confronto Epistemico e Falsificacao sobre Dataset B."""

import json
from pathlib import Path
import pytest

from application.run_falsification_cycle import execute_dataset_b_falsification
from domain import Claim, ConflictRecord, EpistemicStatus


def test_falsification_cycle_dataset_b():
    output_report = execute_dataset_b_falsification()

    assert output_report["falsification_phenomenon"] == "CELL-LAB-001"
    assert output_report["dataset_evaluated"] == "DTS-CELL-LAB-001-FALSIFICATION"

    comparison = output_report["comparison"]
    assert comparison["verdict"] == "DIVERGENT"

    metrics = comparison["metrics"]
    assert metrics["sample_count"] == 11
    # O modelo falha na grande maioria dos pontos sob carga
    assert metrics["within_2_sigma_count"] <= 4
    assert metrics["r_squared"] < 0.0  # R2 negativo comprova que o modelo e pior que a media dos dados
    assert metrics["max_z_score"] > 30.0  # Escore z de quase 50 sigma na forca de parada

    # Valida o ConflictRecord gerado (INV-CONFLICT-001)
    conflict_data = output_report["conflict_record"]
    conflict = ConflictRecord.model_validate(conflict_data)
    assert conflict.evidence_a_id is not None
    assert conflict.evidence_b_id is not None
    assert "F_load" in conflict.conditions_comparison["model_assumption"] or "unloaded" in conflict.conditions_comparison["model_assumption"]

    # Valida o Claim de falsificacao (status CONTRADICTED)
    claim_data = output_report["falsification_claim"]
    claim = Claim.model_validate(claim_data)
    assert claim.epistemic_record.status == EpistemicStatus.CONTRADICTED
    assert len(claim.conflicting_evidence_ids) >= 8
    assert len(claim.supporting_evidence_ids) == 0


def test_falsification_report_file_integrity():
    project_root = Path(__file__).resolve().parent.parent.parent
    report_file = project_root / "data" / "derived" / "cell_lab_001" / "falsification_report_dataset_b.json"

    assert report_file.exists(), "Relatorio em disco deve existir."

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["comparison"]["verdict"] == "DIVERGENT"
    assert len(data["comparison"]["point_comparisons"]) == 11
