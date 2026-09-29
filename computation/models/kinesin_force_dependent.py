"""Modelo Mecanoquimico Concorrente Dependente de Forca (M2 - Ciclo 10)."""

import math
from typing import Dict, Any, Optional
from domain import (
    Model,
    Parameter,
    ParameterEpistemicOrigin,
    ModelValidationStatus,
    StandardUnit,
    Quantity,
    DataTier,
    EpistemicStatus,
    Prediction,
)


def evaluate_force_dependent_velocity(
    atp_concentration_uM: float,
    load_force_pN: float = 0.0,
    k_cat_0_per_s: float = 108.33,
    k_m_0_uM: float = 101.80,
    delta_characteristic_nm: float = 0.10,
    stall_force_pN: float = 6.13,
    stall_exponent: float = 2.05,
    step_size_nm: float = 8.2,
    temperature_degC: float = 24.0,
) -> float:
    """Calcula velocidade segundo modelo com barreira de energia sensivel a forca (Bell/Kramers).

    k_cat(F) = k_cat_0 * exp(-F * delta / k_B*T)
    K_m(F)   = K_m_0 * exp(+0.5 * F * delta / k_B*T)
    stall_fac = (1 - (F / F_stall)^stall_exponent)
    Sob F >= F_stall, a velocidade cessa estritamente (v = 0).
    """
    if atp_concentration_uM <= 0.0 or load_force_pN >= stall_force_pN:
        return 0.0

    # Constante de Boltzmann * Temperatura (em pN * nm)
    # k_B = 1.380649e-23 J/K = 0.01380649 pN*nm/K
    t_kelvin = 273.15 + temperature_degC
    kb_t_pn_nm = 0.01380649 * t_kelvin  # ~4.10 pN*nm a 24C

    # Modulacao de Bell/Kramers sobre a taxa catalitica
    mechanical_work = load_force_pN * delta_characteristic_nm
    k_cat_f = k_cat_0_per_s * math.exp(-mechanical_work / kb_t_pn_nm)

    # Modulacao de afinidade aparente de Michaelis
    km_f = k_m_0_uM * math.exp(0.5 * mechanical_work / kb_t_pn_nm)

    # Fator estolado de cooperatividade conformacional
    stall_ratio = load_force_pN / stall_force_pN
    stall_factor = max(0.0, 1.0 - (stall_ratio ** stall_exponent))

    step_rate = (k_cat_f * atp_concentration_uM) / (km_f + atp_concentration_uM)
    velocity_um_s = step_rate * (step_size_nm / 1000.0) * stall_factor
    return max(0.0, velocity_um_s)


class KinesinForceDependentModel:
    """Classe executavel do Modelo M2 (KIF5B 4-State Force-Dependent)."""

    def __init__(
        self,
        k_cat_0: float = 108.33,
        k_m_0: float = 101.80,
        delta: float = 0.10,
        stall_force: float = 6.13,
        stall_exponent: float = 2.05,
        step_size: float = 8.2,
    ):
        self.k_cat_0 = k_cat_0
        self.k_m_0 = k_m_0
        self.delta = delta
        self.stall_force = stall_force
        self.stall_exponent = stall_exponent
        self.step_size = step_size
        self.model_def = build_kif5b_force_dependent_model()

    def predict_velocity(self, atp_uM: float, load_pN: float = 0.0) -> float:
        return evaluate_force_dependent_velocity(
            atp_concentration_uM=atp_uM,
            load_force_pN=load_pN,
            k_cat_0_per_s=self.k_cat_0,
            k_m_0_uM=self.k_m_0,
            delta_characteristic_nm=self.delta,
            stall_force_pN=self.stall_force,
            stall_exponent=self.stall_exponent,
            step_size_nm=self.step_size,
        )

    def is_within_envelope(self, atp_uM: float, load_pN: float) -> bool:
        """M2 e valido sob toda a faixa observada [0.0, 6.0] pN e [2.0, 2000.0] uM."""
        return (2.0 <= atp_uM <= 2000.0) and (0.0 <= load_pN <= 6.0)


def build_kif5b_force_dependent_model() -> Model:
    """Constroi a definicao formal do Modelo M2: Mecanoquimico com Sensibilidade a Forca."""

    param_kcat = Parameter(
        name="k_cat_0",
        description="Taxa catalitica maxima de turnover sob forca nula",
        unit=StandardUnit.PER_SECOND,
        default_value=108.33,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        evidence_id="DTS-CELL-LAB-001-COMBINED",
        sensitivity_bounds=[90.0, 130.0],
    )

    param_km = Parameter(
        name="K_m_0",
        description="Constante aparente de Michaelis sob forca nula",
        unit=StandardUnit.MICROMOLAR,
        default_value=101.80,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        evidence_id="DTS-CELL-LAB-001-COMBINED",
        sensitivity_bounds=[70.0, 130.0],
    )

    param_step = Parameter(
        name="step_size",
        description="Deslocamento unitario discreto por hidrolise",
        unit=StandardUnit.NANOMETER,
        default_value=8.2,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="EVI-SVOBODA-1993-STEP",
        sensitivity_bounds=[8.0, 8.4],
    )

    param_delta = Parameter(
        name="delta_transition_distance",
        description="Distancia caracteristica de transicao mecânica do neck linker",
        unit=StandardUnit.NANOMETER,
        default_value=0.10,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        sensitivity_bounds=[0.05, 0.50],
    )

    param_stall = Parameter(
        name="stall_force",
        description="Forca de parada assintotica do motor",
        unit=StandardUnit.PICONEWTON,
        default_value=6.13,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        evidence_id="DTS-CELL-LAB-001-FALSIFICATION",
        sensitivity_bounds=[5.8, 6.5],
    )

    param_exponent = Parameter(
        name="stall_exponent",
        description="Expoente de cooperatividade conformacional proximo ao stall",
        unit=StandardUnit.DIMENSIONLESS,
        default_value=2.05,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        sensitivity_bounds=[1.5, 3.0],
    )

    model = Model(
        id="MOD-KIF5B-4STATE-FORCE-DEPENDENT",
        name="KIF5B_4State_ForceDependent_Kramers",
        description="Modelo mecanoquimico multivariado acoplando turnover cinetico a barreira de forca contraria (Bell/Kramers) e cooperatividade conformacional.",
        target_phenomenon="KIF5B_force_velocity_and_stall",
        assumptions=[
            "Transicoes conformacionais do neck linker possuem barreira de ativacao modificada pela forca externa contraria (W = F * delta).",
            "A afinidade aparente para ATP sofre desaceleracao dependente de deformacao elástica.",
            "A velocidade cessa assintoticamente ao atingir a forca de parada de ~6.13 pN com expoente nao-linear.",
            "O acoplamento estequiometrico mantem 1 ATP hidrolisado por passo mecânico de 8.2 nm.",
        ],
        parameters=[param_kcat, param_km, param_step, param_delta, param_stall, param_exponent],
        inputs=["atp_concentration_uM", "load_force_pN"],
        outputs=["velocity_um_s"],
        equations_or_algorithm_description="k_cat(F) = k_cat_0 * exp(-F*delta / k_B*T); K_m(F) = K_m_0 * exp(0.5*F*delta / k_B*T); v(F, [ATP]) = k_step(F, [ATP]) * d_step * (1 - (F/F_stall)^2.05)",
        implementation_reference="computation.models.kinesin_force_dependent:evaluate_force_dependent_velocity",
        source_reference="Visscher, Schnitzer, Block (Nature 1999, DOI: 10.1038/22146)",
        validation_status=ModelValidationStatus.VALIDATED_WITHIN_BOUNDS,
    )

    return model
