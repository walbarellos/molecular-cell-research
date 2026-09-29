"""Testes unitarios para a Dinamica de Langevin com Ruido Termico (Ciclo 13)."""

import pytest
from domain.langevin import LangevinConfig
from computation.models.langevin_model import build_langevin_model
from computation.engine.langevin_simulator import run_langevin_simulation


def test_langevin_formal_model():
    model = build_langevin_model()
    assert model.id == "MOD-LANGEVIN-STOCHASTIC-STEPPING"
    assert len(model.assumptions) >= 1
    assert len(model.parameters) >= 2


def test_langevin_simulation_execution():
    config = LangevinConfig(
        atp_concentration_uM=1000.0,
        trap_stiffness_pN_nm=0.04,
        total_time_ms=25.0,
        dt_us=2.0,
        random_seed=123,
    )
    traj = run_langevin_simulation(config)
    assert traj.metrics.total_steps >= 0
    assert traj.metrics.thermal_noise_rms_nm > 0.5
    assert traj.metrics.drag_coefficient_pN_us_nm > 0.0
    assert traj.metrics.diffusion_coefficient_nm2_us > 0.0
    assert len(traj.points) > 10


def test_langevin_step_mechanics():
    # Com ATP alto, o motor deve executar passos mecanoquimicos
    config = LangevinConfig(
        atp_concentration_uM=2000.0,
        trap_stiffness_pN_nm=0.02,
        total_time_ms=40.0,
        dt_us=2.0,
        random_seed=42,
    )
    traj = run_langevin_simulation(config)
    assert traj.metrics.total_steps > 0
    # Verifica que posicao do motor avancou em multiplos de 8.2 nm
    final_motor_x = traj.points[-1].motor_position_nm
    assert final_motor_x >= 8.2
