"""Motor de Simulacao Estocastica de Competicao Motora (Tug-of-War Gillespie).

Executa a trajetoria de Monte Carlo cinetico e calcula o estado estacionario da
equacao mestra bidimensional P(n+, n-).
"""

import math
import random
from typing import Dict, List, Tuple
import numpy as np

from domain.tug_of_war import (
    TugOfWarConfig,
    TugOfWarState,
    TugOfWarMetrics,
    TugOfWarSimulationResult,
)
from computation.models.tug_of_war import (
    get_default_kinesin_spec,
    get_default_dynein_spec,
    compute_tug_of_war_kinetics,
)


def compute_tug_of_war_steady_state(config: TugOfWarConfig) -> Dict[str, float]:
    """Calcula a distribuicao estacionaria analitica da equacao mestra de Markov."""
    kinesin = config.kinesin_spec or get_default_kinesin_spec()
    dynein = config.dynein_spec or get_default_dynein_spec()
    n_k_max = config.num_kinesins
    n_d_max = config.num_dyneins
    total_states = (n_k_max + 1) * (n_d_max + 1)

    def state_idx(nk: int, nd: int) -> int:
        return nk * (n_d_max + 1) + nd

    # Constroi matriz geradora Q (taxas infinitesimais)
    q = np.zeros((total_states, total_states), dtype=float)

    for nk in range(n_k_max + 1):
        for nd in range(n_d_max + 1):
            i = state_idx(nk, nd)
            v_c, f_k, f_d, tens, st = compute_tug_of_war_kinetics(
                nk, nd, kinesin, dynein, config.external_load_pN
            )

            # Taxas de transicao
            # 1. Ligacao de Kinesina
            if nk < n_k_max:
                rate_k_bind = (n_k_max - nk) * kinesin.binding_rate_per_s
                j = state_idx(nk + 1, nd)
                q[i, j] += rate_k_bind

            # 2. Desligamento de Kinesina (Bell)
            if nk > 0:
                rate_k_unbind = nk * kinesin.unbinding_rate_0_per_s * math.exp(f_k / kinesin.detachment_force_pN)
                j = state_idx(nk - 1, nd)
                q[i, j] += rate_k_unbind

            # 3. Ligacao de Dineina
            if nd < n_d_max:
                rate_d_bind = (n_d_max - nd) * dynein.binding_rate_per_s
                j = state_idx(nk, nd + 1)
                q[i, j] += rate_d_bind

            # 4. Desligamento de Dineina (Bell)
            if nd > 0:
                rate_d_unbind = nd * dynein.unbinding_rate_0_per_s * math.exp(f_d / dynein.detachment_force_pN)
                j = state_idx(nk, nd - 1)
                q[i, j] += rate_d_unbind

    # Diagonal de Q: q_ii = - sum_{j != i} q_ij
    for i in range(total_states):
        q[i, i] = -np.sum(q[i, :]) + q[i, i]

    # Resolve P * Q = 0 com sum(P) = 1
    # Substitui uma linha por restricao de normalizacao
    a = q.T.copy()
    a[-1, :] = 1.0
    b = np.zeros(total_states, dtype=float)
    b[-1] = 1.0

    try:
        p_ss, _, _, _ = np.linalg.lstsq(a, b, rcond=None)
        p_ss = np.maximum(0.0, p_ss)
        p_ss /= np.sum(p_ss)
    except Exception:
        # Fallback uniforme
        p_ss = np.ones(total_states) / total_states

    prob_plus = 0.0
    prob_minus = 0.0
    prob_pause = 0.0
    prob_unbound = 0.0

    distribution = {}
    for nk in range(n_k_max + 1):
        for nd in range(n_d_max + 1):
            idx = state_idx(nk, nd)
            p = float(p_ss[idx])
            distribution[f"state_{nk}_{nd}"] = round(p, 4)
            v_c, _, _, _, st = compute_tug_of_war_kinetics(nk, nd, kinesin, dynein, config.external_load_pN)
            if st == "PLUS_END_MOTION":
                prob_plus += p
            elif st == "MINUS_END_MOTION":
                prob_minus += p
            elif st == "TUG_OF_WAR_PAUSE":
                prob_pause += p
            elif st == "UNBOUND":
                prob_unbound += p

    distribution["summary_p_plus"] = round(prob_plus, 4)
    distribution["summary_p_minus"] = round(prob_minus, 4)
    distribution["summary_p_pause"] = round(prob_pause, 4)
    distribution["summary_p_unbound"] = round(prob_unbound, 4)
    return distribution


def run_tug_of_war_simulation(config: TugOfWarConfig) -> TugOfWarSimulationResult:
    """Executa a simulacao estocastica pelo Algoritmo Direto de Gillespie."""
    if config.random_seed is not None:
        rng = random.Random(config.random_seed)
    else:
        rng = random.Random()

    kinesin = config.kinesin_spec or get_default_kinesin_spec()
    dynein = config.dynein_spec or get_default_dynein_spec()
    n_k_max = config.num_kinesins
    n_d_max = config.num_dyneins

    # Estado inicial: carga acoplada com 1 motor de cada equipe
    nk = min(n_k_max, 1)
    nd = min(n_d_max, 1)
    t = 0.0
    x = 0.0

    trajectory: List[TugOfWarState] = []

    # Estatisticas agregadas
    time_plus = 0.0
    time_minus = 0.0
    time_pause = 0.0
    time_unbound = 0.0
    reversals = 0
    prev_dir = 0  # +1 for plus, -1 for minus, 0 for pause

    weighted_nk_sum = 0.0
    weighted_nd_sum = 0.0

    # Grava estado inicial
    v_c, f_k, f_d, tens, st = compute_tug_of_war_kinetics(nk, nd, kinesin, dynein, config.external_load_pN)
    trajectory.append(
        TugOfWarState(
            time_s=0.0,
            bound_kinesins=nk,
            bound_dyneins=nd,
            cargo_velocity_nm_s=round(v_c, 2),
            cargo_position_nm=0.0,
            tension_force_pN=round(tens, 2),
            state_classification=st,
        )
    )

    max_steps = 15000
    step = 0

    while t < config.simulation_duration_s and step < max_steps:
        step += 1
        v_c, f_k, f_d, tens, st = compute_tug_of_war_kinetics(nk, nd, kinesin, dynein, config.external_load_pN)

        # Taxas dos 4 eventos possiveis
        w_k_bind = (n_k_max - nk) * kinesin.binding_rate_per_s if nk < n_k_max else 0.0
        w_k_unbind = nk * kinesin.unbinding_rate_0_per_s * math.exp(f_k / kinesin.detachment_force_pN) if nk > 0 else 0.0
        w_d_bind = (n_d_max - nd) * dynein.binding_rate_per_s if nd < n_d_max else 0.0
        w_d_unbind = nd * dynein.unbinding_rate_0_per_s * math.exp(f_d / dynein.detachment_force_pN) if nd > 0 else 0.0

        total_rate = w_k_bind + w_k_unbind + w_d_bind + w_d_unbind

        if total_rate <= 1e-12:
            # Estado sem transicoes possiveis
            break

        # Gillespie tempo de espera
        u1 = max(1e-15, rng.random())
        tau = -math.log(u1) / total_rate

        # Limita ao tempo maximo de simulacao
        dt = min(tau, config.simulation_duration_s - t)
        t += dt
        x += v_c * dt

        # Integra tempos e pesos
        if st == "PLUS_END_MOTION":
            time_plus += dt
            current_dir = 1
        elif st == "MINUS_END_MOTION":
            time_minus += dt
            current_dir = -1
        elif st == "TUG_OF_WAR_PAUSE":
            time_pause += dt
            current_dir = 0
        else:
            time_unbound += dt
            current_dir = 0

        if prev_dir != 0 and current_dir != 0 and prev_dir != current_dir:
            reversals += 1
        if current_dir != 0:
            prev_dir = current_dir

        weighted_nk_sum += nk * dt
        weighted_nd_sum += nd * dt

        # Seleciona qual evento ocorreu
        u2 = rng.random() * total_rate
        cum = 0.0

        cum += w_k_bind
        if u2 <= cum:
            nk += 1
        else:
            cum += w_k_unbind
            if u2 <= cum:
                nk = max(0, nk - 1)
            else:
                cum += w_d_bind
                if u2 <= cum:
                    nd += 1
                else:
                    nd = max(0, nd - 1)

        # Atualiza cinematica pos-evento
        v_next, _, _, tens_next, st_next = compute_tug_of_war_kinetics(
            nk, nd, kinesin, dynein, config.external_load_pN
        )

        # Subamostragem para manter a trajetoria enxuta (max ~500 pontos)
        if len(trajectory) < 500 or (step % 5 == 0) or t >= config.simulation_duration_s:
            trajectory.append(
                TugOfWarState(
                    time_s=round(t, 4),
                    bound_kinesins=nk,
                    bound_dyneins=nd,
                    cargo_velocity_nm_s=round(v_next, 2),
                    cargo_position_nm=round(x, 2),
                    tension_force_pN=round(tens_next, 2),
                    state_classification=st_next,
                )
            )

    tot_t = max(1e-6, t)
    metrics = TugOfWarMetrics(
        total_time_s=round(tot_t, 3),
        total_distance_nm=round(x, 2),
        net_velocity_nm_s=round(x / tot_t, 2),
        fraction_plus_end=round(time_plus / tot_t, 4),
        fraction_minus_end=round(time_minus / tot_t, 4),
        fraction_pause_tug_of_war=round(time_pause / tot_t, 4),
        fraction_unbound=round(time_unbound / tot_t, 4),
        directional_reversals=reversals,
        mean_kinesins_engaged=round(weighted_nk_sum / tot_t, 2),
        mean_dyneins_engaged=round(weighted_nd_sum / tot_t, 2),
    )

    steady_state = compute_tug_of_war_steady_state(config)

    return TugOfWarSimulationResult(
        config=config,
        metrics=metrics,
        trajectory=trajectory,
        steady_state_distribution=steady_state,
    )
