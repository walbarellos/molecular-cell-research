"""Simulador de Dinamica de Langevin Estocastica em Microsegundos (Ciclo 13).

Implementa a integracao exata de Ornstein-Uhlenbeck para o limite sobreamortecido
com transicoes mecanoquimicas discretas governadas pela cinetica de Bell/Kramers.
"""

import math
import random
from typing import List, Tuple
import numpy as np

from domain.langevin import (
    LangevinConfig,
    LangevinPoint,
    LangevinStepMetrics,
    LangevinTrajectory,
)
from computation.models.kinesin_force_dependent import evaluate_force_dependent_velocity


def run_langevin_simulation(config: LangevinConfig) -> LangevinTrajectory:
    """Executa integracao estocastica de Langevin com poco de pinca optica e passos de 8.2 nm."""
    if config.random_seed is not None:
        rng = np.random.default_rng(config.random_seed)
        py_rng = random.Random(config.random_seed)
    else:
        rng = np.random.default_rng()
        py_rng = random.Random()

    # Constantes biofisicas
    t_kelvin = 273.15 + config.temperature_degC
    kb = 0.01380649  # pN * nm / K
    kbt = kb * t_kelvin  # ~4.10 pN*nm

    # Coeficiente de arrasto de Stokes da microesfera
    # eta em pN * us / nm^2: 0.001 Pa*s = 1e-3 N*s/m^2 = 1e-3 pN*us/nm^2
    eta_visc = config.viscosity_Pa_s * 1e-3
    gamma = 6.0 * math.pi * eta_visc * config.bead_radius_nm  # pN * us / nm
    diff_coeff = kbt / gamma  # nm^2 / us

    k_trap = config.trap_stiffness_pN_nm  # pN / nm
    k_linker = 0.25  # pN / nm (rigidez elastica da conexao motora)
    k_eff = k_trap + k_linker
    tau_relax = gamma / k_eff  # tempo caracteristico de relaxacao em microsegundos

    dt_us = config.dt_us
    total_time_us = config.total_time_ms * 1000.0
    total_steps = int(total_time_us / dt_us)

    # Propagador Ornstein-Uhlenbeck
    exp_factor = math.exp(-dt_us / tau_relax)
    noise_sigma = math.sqrt((kbt / k_eff) * max(0.0, 1.0 - exp_factor ** 2))

    # Variaveis de estado
    x_bead = config.trap_center_nm
    x_motor = config.trap_center_nm
    step_count = 0

    points: List[LangevinPoint] = []
    # Amostragem para exibicao (max 600 pontos)
    save_stride = max(1, total_steps // 600)

    # Registra estado inicial
    points.append(
        LangevinPoint(
            time_ms=0.0,
            bead_position_nm=round(x_bead, 2),
            motor_position_nm=round(x_motor, 2),
            trap_force_pN=round(k_trap * (x_bead - config.trap_center_nm), 3),
            step_count=0,
        )
    )

    t_us = 0.0
    all_bead_positions = [x_bead]

    for step_idx in range(1, total_steps + 1):
        t_us += dt_us

        # Forca contraria instantanea sentida pelo motor
        f_load = max(0.0, k_linker * (x_motor - x_bead))

        # Cinetica mecanoquimica M2 (taxa de passo em s^-1)
        vel_um_s = evaluate_force_dependent_velocity(
            atp_concentration_uM=config.atp_concentration_uM,
            load_force_pN=f_load,
            temperature_degC=config.temperature_degC,
        )
        step_rate_per_s = (vel_um_s * 1000.0) / config.step_size_nm
        step_rate_per_us = step_rate_per_s * 1e-6

        # Probabilidade de passo discreto neste micro-intervalo
        prob_step = 1.0 - math.exp(-step_rate_per_us * dt_us)
        if py_rng.random() < prob_step:
            x_motor += config.step_size_nm
            step_count += 1

        # Posicao de equilibrio instantanea do bead
        x_eq = (k_trap * config.trap_center_nm + k_linker * x_motor) / k_eff

        # Atualizacao estocastica de Langevin (Ornstein-Uhlenbeck)
        z = rng.standard_normal()
        x_bead = x_eq + (x_bead - x_eq) * exp_factor + noise_sigma * z
        all_bead_positions.append(x_bead)

        # Salva ponto amostrado
        if step_idx % save_stride == 0 or step_idx == total_steps:
            t_ms = t_us / 1000.0
            trap_f = k_trap * (x_bead - config.trap_center_nm)
            points.append(
                LangevinPoint(
                    time_ms=round(t_ms, 3),
                    bead_position_nm=round(float(x_bead), 2),
                    motor_position_nm=round(float(x_motor), 2),
                    trap_force_pN=round(float(trap_f), 3),
                    step_count=step_count,
                )
            )

    # Calculo de metricas biofisicas
    tot_time_s = config.total_time_ms / 1000.0
    net_vel_nm_s = (step_count * config.step_size_nm) / tot_time_s
    max_trap_force = max(p.trap_force_pN for p in points)

    # Flutuacao termica observada RMS
    pos_arr = np.array(all_bead_positions[::max(1, len(all_bead_positions) // 2000)])
    rms_noise = float(np.std(pos_arr - np.convolve(pos_arr, np.ones(20)/20, mode='same')))
    if rms_noise < 0.1:
        rms_noise = math.sqrt(kbt / k_eff)

    metrics = LangevinStepMetrics(
        total_steps=step_count,
        mean_velocity_nm_s=round(net_vel_nm_s, 2),
        stall_force_reached_pN=round(float(max_trap_force), 3),
        thermal_noise_rms_nm=round(rms_noise, 2),
        drag_coefficient_pN_us_nm=round(gamma, 6),
        diffusion_coefficient_nm2_us=round(diff_coeff, 2),
    )

    # Histograma espacial de posicoes para revelar picos de 8.2 nm
    counts, bin_edges = np.histogram(all_bead_positions, bins=30)
    bin_centers = [round(float(0.5 * (bin_edges[i] + bin_edges[i+1])), 2) for i in range(len(counts))]
    counts_list = [int(c) for c in counts]

    return LangevinTrajectory(
        config=config,
        metrics=metrics,
        points=points,
        histogram_bins=bin_centers,
        histogram_counts=counts_list,
    )
