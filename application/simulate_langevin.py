"""Servico de Aplicacao para Execucao de Dinamica Langevin com Ruido Termico (Ciclo 13)."""

from typing import Optional
from domain.langevin import (
    LangevinConfig,
    LangevinTrajectory,
)
from computation.engine.langevin_simulator import run_langevin_simulation


def execute_langevin_cycle(
    atp_uM: float = 1000.0,
    trap_stiffness_pN_nm: float = 0.04,
    total_time_ms: float = 50.0,
    dt_us: float = 2.0,
    seed: Optional[int] = 42,
) -> LangevinTrajectory:
    """Executa ensaio computacional estocastico continuo de Langevin."""
    config = LangevinConfig(
        atp_concentration_uM=atp_uM,
        trap_stiffness_pN_nm=trap_stiffness_pN_nm,
        total_time_ms=total_time_ms,
        dt_us=dt_us,
        random_seed=seed,
    )
    return run_langevin_simulation(config)
