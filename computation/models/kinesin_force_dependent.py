"""Modelo Mecanoquimico Concorrente Dependente de Forca (M2 - Ciclo 09)."""

import math
from typing import Optional
from domain import (
    Model,
    Parameter,
    ParameterEpistemicOrigin,
    ModelValidationStatus,
    StandardUnit,
)


def evaluate_force_dependent_velocity(
    atp_concentration_uM: float,
    load_force_pN: float = 0.0,
    k_cat_0_per_s: float = 104.0,
    k_m_0_uM: float = 95.0,
    delta_characteristic_nm: float = 2.0,
    stall_force_pN: float = 6.0,
    step_size_nm: float = 8.2,
    temperature_degC: float = 24.0,
) -> float:
    """Calcula velocidade segundo modelo com barreira de energia sensivel a forca (Bell/Kramers).

    k_cat(F) = k_cat_0 * exp(-F * delta / k_B*T)
    Sob F >= F_stall, a velocidade cessa (v = 0).
    """
    if atp_concentration_uM <= 0.0 or load_force_pN >= stall_force_pN:
        return 0.0

    # Constante de Boltzmann * Temperatura (em pN * nm)
    # k_B = 1.380649e-23 J/K = 0.01380649 pN*nm/K
    t_kelvin = 273.15 + temperature_degC
    kb_t_pn_nm = 0.01380649 * t_kelvin  # ~4.1 pN*nm a 24C

    # Modulacao de Bell sobre a taxa catalitica
    mechanical_work = load_force_pN * delta_characteristic_nm
    k_cat_f = k_cat_0_per_s * math.exp(-mechanical_work / kb_t_pn_nm)

    # Modulacao de afinidade aparente
    km_f = k_m_0_uM * math.exp(0.5 * mechanical_work / kb_t_pn_nm)

    # Fator de desaceleracao linear proximo ao stall
    stall_factor = max(0.0, 1.0 - (load_force_pN / stall_force_pN) ** 1.5)

    step_rate = (k_cat_f * atp_concentration_uM) / (km_f + atp_concentration_uM)
    velocity_um_s = step_rate * (step_size_nm / 1000.0) * stall_factor
    return max(0.0, velocity_um_s)


def build_kif5b_force_dependent_model() -> Model:
    """Constroi o Modelo M2: Mecanoquimico de 4 Estados com Sensibilidade a Forca."""

    param_kcat = Parameter(
        name="k_cat_0",
        description="Taxa catalitica maxima sob forca nula",
        unit=StandardUnit.PER_SECOND,
        default_value=104.0,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="DTS-CELL-LAB-001-CALIBRATION",
        sensitivity_bounds=[90.0, 120.0],
    )

    param_km = Parameter(
        name="K_m_0",
        description="Constante aparente de Michaelis sob forca nula",
        unit=StandardUnit.MICROMOLAR,
        default_value=95.0,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="DTS-CELL-LAB-001-CALIBRATION",
        sensitivity_bounds=[70.0, 120.0],
    )

    param_step = Parameter(
        name="step_size",
        description="Deslocamento unitario discreto",
        unit=StandardUnit.NANOMETER,
        default_value=8.2,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="EVI-SVOBODA-1993-STEP",
        sensitivity_bounds=[8.0, 8.4],
    )

    param_delta = Parameter(
        name="delta_transition_distance",
        description="Distancia caracteristica de deformacao ate o estado de transicao mecânica",
        unit=StandardUnit.NANOMETER,
        default_value=2.0,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        sensitivity_bounds=[1.0, 3.5],
    )

    param_stall = Parameter(
        name="stall_force",
        description="Forca de parada estolada do motor",
        unit=StandardUnit.PICONEWTON,
        default_value=6.0,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="DTS-CELL-LAB-001-FALSIFICATION",
        sensitivity_bounds=[5.0, 7.5],
    )

    model = Model(
        id="MOD-KIF5B-4STATE-FORCE-DEPENDENT",
        name="KIF5B_4State_ForceDependent_Kramers",
        description="Modelo mecanoquimico avancado acoplando o ciclo de hidrolise a dependencia exponencial de forca contraria (teoria de Bell/Kramers).",
        target_phenomenon="KIF5B_force_velocity_and_stall",
        assumptions=[
            "Transicoes conformacionais do neck linker possuem barreira de ativacao modificada pela forca externa contraria (W = F * delta).",
            "A taxa de turnover desacelera exponencialmente conforme a forca aproxima-se da forca de parada (~6 pN).",
            "A hidrolise de ATP permanece estritamente acoplada a 1 passo mecânico de 8.2 nm.",
        ],
        parameters=[param_kcat, param_km, param_step, param_delta, param_stall],
        inputs=["atp_concentration_uM", "load_force_pN"],
        outputs=["velocity_um_s"],
        equations_or_algorithm_description="k_cat(F) = k_cat_0 * exp(-F*delta / k_B*T); v(F, [ATP]) = k_step(F, [ATP]) * d_step * (1 - (F/F_stall)^1.5)",
        implementation_reference="computation.models.kinesin_force_dependent:evaluate_force_dependent_velocity",
        source_reference="Visscher, Schnitzer, Block (Nature 1999, DOI: 10.1038/22146)",
        validation_status=ModelValidationStatus.PROVISIONALLY_CONSISTENT,
    )

    return model
