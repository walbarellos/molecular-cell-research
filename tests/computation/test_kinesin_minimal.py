"""Testes do Modelo Mecanomolecular Minimo KIF5B e Motores de Simulacao/Calibracao (L5)."""

import json
from pathlib import Path
import pytest

from domain import (
    Model,
    Simulation,
    Prediction,
    Observation,
    StandardUnit,
    DataTier,
    EpistemicStatus,
)
from computation.formalisms.kinetics import (
    evaluate_michaelis_menten_velocity,
    simulate_gillespie_trajectory,
)
from computation.models.kinesin_minimal import build_kif5b_minimal_model
from computation.engine.calibration import calibrate_kif5b_from_observations
from computation.engine.simulator import run_kif5b_simulation
from validation import verify_inv_model_001, verify_inv_repro_001, verify_inv_prediction_001


def test_analytical_velocity_properties():
    # v([ATP] = 0) == 0
    v_zero = evaluate_michaelis_menten_velocity(
        atp_concentration_uM=0.0,
        k_cat_per_s=100.0,
        k_m_uM=100.0,
        step_size_nm=8.2,
    )
    assert v_zero == 0.0

    # v([ATP] = K_m) == V_max / 2
    # V_max = 100.0 * 0.0082 = 0.82 um/s -> v = 0.41 um/s
    v_half = evaluate_michaelis_menten_velocity(
        atp_concentration_uM=100.0,
        k_cat_per_s=100.0,
        k_m_uM=100.0,
        step_size_nm=8.2,
    )
    assert pytest.approx(v_half, abs=1e-5) == 0.41

    # Validacao de erros com parametros negativos
    with pytest.raises(ValueError):
        evaluate_michaelis_menten_velocity(atp_concentration_uM=-5.0, k_cat_per_s=100.0, k_m_uM=100.0)
    with pytest.raises(ValueError):
        evaluate_michaelis_menten_velocity(atp_concentration_uM=10.0, k_cat_per_s=-1.0, k_m_uM=100.0)


def test_stochastic_gillespie_determinism_and_convergence():
    # Mesma semente gera exatamente os mesmos passos e trajetoria
    res1 = simulate_gillespie_trajectory(
        atp_concentration_uM=1000.0,
        k_cat_per_s=104.0,
        k_m_uM=95.0,
        max_duration_s=2.0,
        random_seed=12345,
    )
    res2 = simulate_gillespie_trajectory(
        atp_concentration_uM=1000.0,
        k_cat_per_s=104.0,
        k_m_uM=95.0,
        max_duration_s=2.0,
        random_seed=12345,
    )
    assert res1["total_steps"] == res2["total_steps"]
    assert res1["final_position_um"] == res2["final_position_um"]
    assert res1["dwell_times_s"] == res2["dwell_times_s"]

    # Sementes distintas produzem trajetorias estocasticas diferentes
    res3 = simulate_gillespie_trajectory(
        atp_concentration_uM=1000.0,
        k_cat_per_s=104.0,
        k_m_uM=95.0,
        max_duration_s=2.0,
        random_seed=99999,
    )
    assert res1["dwell_times_s"] != res3["dwell_times_s"]

    # Trajetoria longa converge para velocidade teorica (~0.778 um/s)
    res_long = simulate_gillespie_trajectory(
        atp_concentration_uM=1000.0,
        k_cat_per_s=104.0,
        k_m_uM=95.0,
        max_duration_s=15.0,
        random_seed=42,
    )
    v_theo = evaluate_michaelis_menten_velocity(1000.0, 104.0, 95.0)
    assert pytest.approx(res_long["mean_velocity_um_s"], rel=0.10) == v_theo


def test_calibration_on_dataset_a():
    project_root = Path(__file__).resolve().parent.parent.parent
    dataset_a_path = project_root / "data" / "derived" / "cell_lab_001" / "dataset_a_calibration.json"

    with open(dataset_a_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    observations = [Observation.model_validate(o) for o in payload["observations"]]
    calib = calibrate_kif5b_from_observations(observations, step_size_nm=8.2)

    # Verifica os parametros ajustados (compatibilidade com Schnitzer & Block 1997)
    # V_max deve estar proximo de 0.85 um/s, k_cat em torno de 104 s^-1 e K_m em torno de 90-100 uM
    assert 0.80 <= calib["v_max_um_s"] <= 0.90
    assert 95.0 <= calib["k_cat_per_s"] <= 115.0
    assert 80.0 <= calib["k_m_uM"] <= 110.0
    assert calib["r_squared"] > 0.99
    assert calib["chi2_reduced"] < 2.0


def test_kif5b_model_and_simulation_invariants():
    model = build_kif5b_minimal_model(k_cat_default=104.0, k_m_default=95.0)
    verify_inv_model_001(model)

    simulation, predictions = run_kif5b_simulation(
        model=model,
        atp_concentrations_uM=[10.0, 100.0, 1000.0],
        mode="analytical",
    )

    verify_inv_repro_001(simulation)
    assert len(predictions) == 3

    for pred in predictions:
        verify_inv_prediction_001(pred)
        assert pred.model_id == model.id
        assert pred.simulation_id == simulation.id
        assert pred.epistemic_record.data_tier == DataTier.GENERATED
        assert pred.epistemic_record.status == EpistemicStatus.PREDICTED
        assert pred.quantity.unit == StandardUnit.MICROMETER_PER_SECOND
        assert pred.quantity.value > 0.0
