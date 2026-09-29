"""Servico de Aplicacao para Execucao de Ensaios de Competicao Motora (Ciclo 12)."""

from typing import Optional
from domain.tug_of_war import (
    TugOfWarConfig,
    TugOfWarSimulationResult,
)
from computation.engine.tug_of_war_simulator import (
    run_tug_of_war_simulation,
    compute_tug_of_war_steady_state,
)


def execute_tug_of_war_cycle(
    num_kinesins: int = 4,
    num_dyneins: int = 4,
    external_load_pN: float = 0.0,
    duration_s: float = 5.0,
    seed: Optional[int] = 42,
) -> TugOfWarSimulationResult:
    """Executa ensaio computacional estocastico de competicao motora vesicular."""
    config = TugOfWarConfig(
        num_kinesins=num_kinesins,
        num_dyneins=num_dyneins,
        external_load_pN=external_load_pN,
        simulation_duration_s=duration_s,
        random_seed=seed,
    )
    return run_tug_of_war_simulation(config)
