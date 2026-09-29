"""Testes unitarios para o modelo de Competicao Motora (Tug-of-War - Ciclo 12)."""

import pytest
from domain.tug_of_war import TugOfWarConfig, MotorDirection
from computation.models.tug_of_war import (
    get_default_kinesin_spec,
    get_default_dynein_spec,
    compute_tug_of_war_kinetics,
    build_tug_of_war_model,
)
from computation.engine.tug_of_war_simulator import (
    run_tug_of_war_simulation,
    compute_tug_of_war_steady_state,
)


def test_motor_specs_defaults():
    kinesin = get_default_kinesin_spec()
    assert kinesin.direction == MotorDirection.PLUS_END
    assert kinesin.stall_force_pN == 6.0
    assert kinesin.unloaded_velocity_nm_s > 0.0

    dynein = get_default_dynein_spec()
    assert dynein.direction == MotorDirection.MINUS_END
    assert dynein.stall_force_pN == 1.25
    assert dynein.unloaded_velocity_nm_s < 0.0


def test_compute_tug_of_war_kinetics():
    kinesin = get_default_kinesin_spec()
    dynein = get_default_dynein_spec()

    # Unbound
    v, fk, fd, tens, st = compute_tug_of_war_kinetics(0, 0, kinesin, dynein)
    assert st == "UNBOUND"
    assert v == 0.0

    # Only kinesins
    v, fk, fd, tens, st = compute_tug_of_war_kinetics(2, 0, kinesin, dynein)
    assert st == "PLUS_END_MOTION"
    assert v > 0.0

    # Only dyneins
    v, fk, fd, tens, st = compute_tug_of_war_kinetics(0, 2, kinesin, dynein)
    assert st == "MINUS_END_MOTION"
    assert v < 0.0

    # Kinesins overpowering dyneins (e.g. 4 kinesins vs 2 dyneins)
    # 4 * 6.0 = 24 pN vs 2 * 1.25 = 2.5 pN
    v, fk, fd, tens, st = compute_tug_of_war_kinetics(4, 2, kinesin, dynein)
    assert st == "PLUS_END_MOTION"
    assert v > 0.0
    assert fd == dynein.stall_force_pN


def test_tug_of_war_simulation_execution():
    config = TugOfWarConfig(
        num_kinesins=4,
        num_dyneins=4,
        external_load_pN=0.0,
        simulation_duration_s=2.0,
        random_seed=42,
    )
    result = run_tug_of_war_simulation(config)
    assert result.metrics.total_time_s > 0.0
    assert len(result.trajectory) > 5
    assert 0.0 <= result.metrics.fraction_plus_end <= 1.0
    assert 0.0 <= result.metrics.fraction_minus_end <= 1.0


def test_tug_of_war_steady_state():
    config = TugOfWarConfig(num_kinesins=2, num_dyneins=2)
    dist = compute_tug_of_war_steady_state(config)
    assert "summary_p_plus" in dist
    assert "summary_p_minus" in dist
    total_p = (
        dist["summary_p_plus"]
        + dist["summary_p_minus"]
        + dist["summary_p_pause"]
        + dist["summary_p_unbound"]
    )
    assert pytest.approx(total_p, abs=0.05) == 1.0


def test_tug_of_war_formal_model():
    model = build_tug_of_war_model()
    assert model.id == "MOD-TUG-OF-WAR-KINESIN-DYNEIN"
    assert len(model.assumptions) >= 1
    assert len(model.parameters) >= 2
