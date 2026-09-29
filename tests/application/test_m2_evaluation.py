"""Testes automatizados do Ciclo 10: Avaliacao Multivariada do Modelo M2 sob Carga."""

import json
from pathlib import Path
import pytest

from application.run_m2_evaluation_cycle import execute_m2_evaluation_cycle

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "derived" / "cell_lab_001"


def test_m2_evaluation_cycle_metrics():
    report = execute_m2_evaluation_cycle()
    metrics = report["metrics"]

    assert report["total_observations_evaluated"] == 21
    assert report["dataset_a_count"] == 10
    assert report["dataset_b_count"] == 11

    # R2 global excelente (> 0.99)
    assert metrics["r_squared"] >= 0.99
    # Chi2 reduzido proximo a 1.0 ou menor
    assert metrics["chi2_reduced"] <= 1.0
    # 100% dos pontos devem estar dentro de 2-sigma
    assert metrics["within_2_sigma_count"] == 21
    assert metrics["within_2_sigma_ratio"] == 1.0
    # Veredito consistente
    assert report["verdict"] == "consistent"


def test_m2_resolves_conflict_and_claims():
    report = execute_m2_evaluation_cycle()

    # Confere resolucao formal do conflito
    conf_res = report["conflict_resolution"]
    assert conf_res["id"] == "CONF-KIF5B-LOAD-001"
    assert conf_res["resolution_status"] == "resolved_by_model_expansion"
    assert conf_res["resolving_model_id"] == "MOD-KIF5B-4STATE-FORCE-DEPENDENT"

    # Confere claim validado
    claim = report["claim"]
    assert claim["id"] == "CLM-VALID-KIF5B-FORCE-M2-001"
    assert claim["epistemic_record"]["status"] == "VALIDATED"
    assert claim["epistemic_record"]["data_tier"] == "DERIVED"
    assert len(claim["supporting_evidence_ids"]) == 21


def test_m2_report_file_integrity():
    report_file = DATA_DIR / "m2_evaluation_report.json"
    assert report_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["model_id"] == "MOD-KIF5B-4STATE-FORCE-DEPENDENT"
    assert len(data["point_evaluations"]) == 21
