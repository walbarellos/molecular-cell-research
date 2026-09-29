"""Testes automatizados do Ciclo 09: Desenho Experimental Discriminatorio (L6)."""

import json
from pathlib import Path
import pytest

from application.run_experimental_design import execute_experimental_design_cycle
from domain import ExperimentDesign, Hypothesis, EpistemicStatus
from analysis.discriminator import evaluate_discriminatory_grid


def test_discriminatory_grid_evaluation():
    evaluations = evaluate_discriminatory_grid(
        atp_grid_uM=[10.0, 1000.0],
        load_grid_pN=[0.0, 2.5, 5.0],
        expected_measurement_sigma=0.030,
    )

    assert len(evaluations) == 6
    # Em carga zero (0.0 pN), M1 e M2 devem ser relativamente proximos (baixo poder discriminatorio)
    unloaded_eval = next(e for e in evaluations if e.load_force_pN == 0.0 and e.atp_concentration_uM == 1000.0)
    assert unloaded_eval.delta_velocity < 0.10

    # Sob alta carga (5.0 pN) e saturacao, M1 e M2 divergem radicalmente
    loaded_eval = next(e for e in evaluations if e.load_force_pN == 5.0 and e.atp_concentration_uM == 1000.0)
    assert loaded_eval.delta_velocity > 0.40
    assert loaded_eval.discriminatory_power_score > 0.95


def test_experimental_design_pipeline_execution():
    output = execute_experimental_design_cycle()

    assert output["cycle"] == "CICLO_09_EXPERIMENTAL_DESIGN"
    assert output["phenomenon"] == "CELL-LAB-001"

    # Valida objeto ExperimentDesign
    des_data = output["optimal_experiment_design"]
    exp_des = ExperimentDesign.model_validate(des_data)
    assert len(exp_des.competing_model_ids) == 2
    assert exp_des.discriminatory_power_score is not None
    assert exp_des.discriminatory_power_score > 0.95
    assert exp_des.target_conditions["load_force_pN"] > 0.0

    # Valida objeto Hypothesis
    hyp_data = output["target_hypothesis"]
    hypo = Hypothesis.model_validate(hyp_data)
    assert hypo.epistemic_record.status == EpistemicStatus.HYPOTHESIS
    assert len(hypo.falsification_criteria) >= 2


def test_experiment_design_file_integrity():
    project_root = Path(__file__).resolve().parent.parent.parent
    report_file = project_root / "data" / "derived" / "cell_lab_001" / "experiment_design_cell_lab_001.json"

    assert report_file.exists(), "Arquivo de desenho experimental deve existir."

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "optimal_experiment_design" in data
    assert "top_5_discriminatory_conditions" in data
    assert len(data["top_5_discriminatory_conditions"]) == 5
