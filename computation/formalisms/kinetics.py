"""Formalismo de Cinética de Michaelis-Menten e gerador estocastico de passos discretos."""

import math
import random
from typing import Dict, List, Tuple


def evaluate_michaelis_menten_velocity(
    atp_concentration_uM: float,
    k_cat_per_s: float,
    k_m_uM: float,
    step_size_nm: float = 8.2,
) -> float:
    """Calcula a velocidade mecanomolecular analitica sem carga (unloaded).

    v([ATP]) = (k_cat * [ATP] / (K_m + [ATP])) * (step_size_nm / 1000)

    Retorna a velocidade em micrômetros por segundo (um/s).
    """
    if atp_concentration_uM < 0.0:
        raise ValueError(f"Concentracao de ATP nao pode ser negativa: {atp_concentration_uM}")
    if k_cat_per_s <= 0.0:
        raise ValueError(f"k_cat deve ser positivo: {k_cat_per_s}")
    if k_m_uM <= 0.0:
        raise ValueError(f"K_m deve ser positivo: {k_m_uM}")
    if step_size_nm <= 0.0:
        raise ValueError(f"step_size deve ser positivo: {step_size_nm}")

    if atp_concentration_uM == 0.0:
        return 0.0

    step_size_um = step_size_nm / 1000.0
    turnover_rate = (k_cat_per_s * atp_concentration_uM) / (k_m_uM + atp_concentration_uM)
    velocity_um_s = turnover_rate * step_size_um
    return velocity_um_s


def simulate_gillespie_trajectory(
    atp_concentration_uM: float,
    k_cat_per_s: float,
    k_m_uM: float,
    step_size_nm: float = 8.2,
    max_duration_s: float = 5.0,
    random_seed: int = 42,
) -> Dict[str, any]:
    """Executa simulacao estocastica de passos de KIF5B via algoritmo de Gillespie.

    A taxa de transicao de passo k_step = (k_cat * [ATP]) / (K_m + [ATP]).
    O tempo de espera tau segue distribuicao exponencial com parametro k_step.
    """
    if atp_concentration_uM <= 0.0:
        return {
            "duration_s": max_duration_s,
            "total_steps": 0,
            "final_position_um": 0.0,
            "mean_velocity_um_s": 0.0,
            "dwell_times_s": [],
            "time_points_s": [0.0],
            "positions_um": [0.0],
        }

    rng = random.Random(random_seed)
    step_rate = (k_cat_per_s * atp_concentration_uM) / (k_m_uM + atp_concentration_uM)
    step_size_um = step_size_nm / 1000.0

    current_time = 0.0
    current_pos_um = 0.0
    time_points = [0.0]
    positions_um = [0.0]
    dwell_times = []

    while current_time < max_duration_s:
        # Gera tempo de espera estocastico: tau = -ln(U) / rate
        u = rng.random()
        while u == 0.0:
            u = rng.random()
        tau = -math.log(u) / step_rate

        if current_time + tau > max_duration_s:
            break

        current_time += tau
        current_pos_um += step_size_um

        dwell_times.append(tau)
        time_points.append(round(current_time, 6))
        positions_um.append(round(current_pos_um, 6))

    mean_v = (current_pos_um / current_time) if current_time > 0 else 0.0

    return {
        "duration_s": current_time,
        "total_steps": len(dwell_times),
        "final_position_um": current_pos_um,
        "mean_velocity_um_s": mean_v,
        "dwell_times_s": dwell_times,
        "time_points_s": time_points,
        "positions_um": positions_um,
    }
