"""Motor de Discriminacao e Desenho Experimental (L6)."""

import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict

from domain import ExperimentDesign
from computation.models.kinesin_minimal import build_kif5b_minimal_model
from computation.formalisms.kinetics import evaluate_michaelis_menten_velocity
from computation.models.kinesin_force_dependent import (
    build_kif5b_force_dependent_model,
    evaluate_force_dependent_velocity,
)


class CandidateConditionEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    atp_concentration_uM: float
    load_force_pN: float
    m1_predicted_velocity: float
    m2_predicted_velocity: float
    delta_velocity: float
    discriminatory_power_score: float  # [0.0, 1.0]
    expected_sigma_um_s: float


def evaluate_discriminatory_grid(
    atp_grid_uM: List[float],
    load_grid_pN: List[float],
    expected_measurement_sigma: float = 0.030,
) -> List[CandidateConditionEvaluation]:
    """Calcula a divergencia teorica entre M1 e M2 para uma grade de condicoes candidatas."""
    results: List[CandidateConditionEvaluation] = []

    for atp in atp_grid_uM:
        for load in load_grid_pN:
            # Predicao M1 (Michaelis-Menten sem forca)
            v_m1 = evaluate_michaelis_menten_velocity(
                atp_concentration_uM=atp,
                k_cat_per_s=103.92,
                k_m_uM=94.63,
                step_size_nm=8.2,
            )

            # Predicao M2 (Mecanoquimico dependente de forca)
            v_m2 = evaluate_force_dependent_velocity(
                atp_concentration_uM=atp,
                load_force_pN=load,
                k_cat_0_per_s=104.0,
                k_m_0_uM=95.0,
                delta_characteristic_nm=2.0,
                stall_force_pN=6.0,
                step_size_nm=8.2,
            )

            delta_v = abs(v_m1 - v_m2)

            # Escore de resolucao normalizado via funcao de saturacao exponencial
            # Se delta_v >> 2*sigma, score -> 1.0 (resolucao categorica)
            scale = 2.0 * expected_measurement_sigma
            score = 1.0 - math.exp(-delta_v / scale) if scale > 0 else 0.0

            results.append(
                CandidateConditionEvaluation(
                    atp_concentration_uM=atp,
                    load_force_pN=load,
                    m1_predicted_velocity=round(v_m1, 5),
                    m2_predicted_velocity=round(v_m2, 5),
                    delta_velocity=round(delta_v, 5),
                    discriminatory_power_score=round(score, 4),
                    expected_sigma_um_s=expected_measurement_sigma,
                )
            )

    # Ordena decrescente por poder discriminatorio
    results.sort(key=lambda r: r.discriminatory_power_score, reverse=True)
    return results


def design_optimal_discriminatory_experiment(
    atp_grid_uM: Optional[List[float]] = None,
    load_grid_pN: Optional[List[float]] = None,
) -> Tuple[ExperimentDesign, List[CandidateConditionEvaluation]]:
    """Gera a proposta formal de ExperimentDesign com a condicao de maxima discriminacao."""
    if atp_grid_uM is None:
        atp_grid_uM = [10.0, 50.0, 200.0, 1000.0, 2000.0]
    if load_grid_pN is None:
        load_grid_pN = [0.0, 1.0, 2.5, 4.0, 5.0, 5.8]

    evaluations = evaluate_discriminatory_grid(atp_grid_uM, load_grid_pN)
    best_candidate = evaluations[0]

    m1 = build_kif5b_minimal_model()
    m2 = build_kif5b_force_dependent_model()

    experiment_design = ExperimentDesign(
        id="EXP-DESIGN-KIF5B-LOAD-DISCRIM-001",
        title="Ensaio de Pinca de Forca Optica para Discriminacao Quimioestatica vs. Mecanoquimica",
        objective=(
            "Discriminar categoricamente entre o modelo quimioestatico (M1) e o modelo mecanoquimico "
            "com acoplamento de Bell (M2) sob regime de alta carga contraria e saturacao de ATP."
        ),
        competing_model_ids=[m1.id, m2.id],
        target_conditions={
            "load_force_pN": best_candidate.load_force_pN,
            "atp_concentration_uM": best_candidate.atp_concentration_uM,
            "temperature_degC": 24.0,
            "buffer": "BRB80",
        },
        proposed_technique="optical_force_clamp",
        predicted_outcomes={
            m1.id: f"Velocidade calculada: {best_candidate.m1_predicted_velocity} um/s (insensivel a carga)",
            m2.id: f"Velocidade calculada: {best_candidate.m2_predicted_velocity} um/s (desaceleracao mecanoquimica)",
        },
        discriminatory_power_score=best_candidate.discriminatory_power_score,
    )

    return experiment_design, evaluations
