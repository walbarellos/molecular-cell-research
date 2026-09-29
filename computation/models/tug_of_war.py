"""Modelo Formal de Competicao Motora (Tug-of-War Kinesin vs. Dynein - Ciclo 12).

Implementa o modelo biofisico estocastico de transporte vesicular bidirecional
conforme Muller, Klumpp & Lipowsky (PNAS 2008).
"""

from typing import Tuple, Dict, Any, List
import math
from domain.model import (
    Model,
    Parameter,
    ParameterEpistemicOrigin,
    ModelValidationStatus,
)
from domain.units import StandardUnit
from domain.tug_of_war import (
    MotorDirection,
    MotorSpeciesSpec,
    TugOfWarConfig,
    TugOfWarState,
)


def get_default_kinesin_spec() -> MotorSpeciesSpec:
    """Parametros biofisicos de referencia da Kinesin-1 (KIF5B)."""
    return MotorSpeciesSpec(
        name="Kinesin-1 (KIF5B)",
        direction=MotorDirection.PLUS_END,
        stall_force_pN=6.0,
        detachment_force_pN=3.0,
        unloaded_velocity_nm_s=800.0,
        unbinding_rate_0_per_s=1.0,
        binding_rate_per_s=5.0,
        step_size_nm=8.2,
    )


def get_default_dynein_spec() -> MotorSpeciesSpec:
    """Parametros biofisicos de referencia da Dineina Citoplasmatica (DYNC1H1)."""
    return MotorSpeciesSpec(
        name="Cytoplasmic Dynein",
        direction=MotorDirection.MINUS_END,
        stall_force_pN=1.25,
        detachment_force_pN=0.75,
        unloaded_velocity_nm_s=-700.0,
        unbinding_rate_0_per_s=0.25,
        binding_rate_per_s=1.6,
        step_size_nm=8.2,
    )


def compute_tug_of_war_kinetics(
    n_plus: int,
    n_minus: int,
    kinesin: MotorSpeciesSpec,
    dynein: MotorSpeciesSpec,
    f_ext_pN: float = 0.0,
) -> Tuple[float, float, float, float, str]:
    """Calcula velocidade da carga, forcas individuais e classificacao de estado.

    Retorna: (v_cargo_nm_s, f_plus_pN, f_minus_pN, tension_pN, state_str)
    """
    if n_plus == 0 and n_minus == 0:
        return 0.0, 0.0, 0.0, 0.0, "UNBOUND"

    if n_plus > 0 and n_minus == 0:
        f_per_k = f_ext_pN / n_plus
        if f_per_k >= kinesin.stall_force_pN:
            v_c = 0.0
        else:
            v_c = kinesin.unloaded_velocity_nm_s * (1.0 - (f_per_k / kinesin.stall_force_pN))
        return max(0.0, v_c), max(0.0, f_per_k), 0.0, 0.0, "PLUS_END_MOTION"

    if n_plus == 0 and n_minus > 0:
        f_per_d = -f_ext_pN / n_minus
        if f_per_d >= dynein.stall_force_pN:
            v_c = 0.0
        else:
            v_c = dynein.unloaded_velocity_nm_s * (1.0 - (f_per_d / dynein.stall_force_pN))
        return min(0.0, v_c), 0.0, max(0.0, f_per_d), 0.0, "MINUS_END_MOTION"

    # Caso n_plus > 0 e n_minus > 0: Tensao competitiva (Tug-of-War)
    total_stall_plus = n_plus * kinesin.stall_force_pN
    total_stall_minus = n_minus * dynein.stall_force_pN

    net_force_balance = total_stall_plus - (total_stall_minus + f_ext_pN)

    if net_force_balance > 0.1:
        # Kinesinas vencem: puxam a carga para plus-end; dineinas resistem em forca de stall
        resisting_force = total_stall_minus + f_ext_pN
        f_per_k = resisting_force / n_plus
        v_c = kinesin.unloaded_velocity_nm_s * (1.0 - (resisting_force / total_stall_plus))
        f_per_d = dynein.stall_force_pN
        tension = total_stall_minus
        state = "PLUS_END_MOTION" if v_c > 50.0 else "TUG_OF_WAR_PAUSE"
        return v_c, f_per_k, f_per_d, tension, state

    elif net_force_balance < -0.1:
        # Dineinas vencem: puxam a carga para minus-end; kinesinas resistem em forca de stall
        resisting_force = total_stall_plus - f_ext_pN
        f_per_d = resisting_force / total_stall_minus
        v_c = dynein.unloaded_velocity_nm_s * (1.0 - (resisting_force / total_stall_minus))
        f_per_k = kinesin.stall_force_pN
        tension = total_stall_plus
        state = "MINUS_END_MOTION" if v_c < -50.0 else "TUG_OF_WAR_PAUSE"
        return v_c, f_per_k, f_per_d, tension, state

    else:
        # Equilibrio de forcas (Tug-of-War puro)
        v_c = 0.0
        f_per_k = kinesin.stall_force_pN
        f_per_d = dynein.stall_force_pN
        tension = total_stall_plus
        return 0.0, f_per_k, f_per_d, tension, "TUG_OF_WAR_PAUSE"


def build_tug_of_war_model() -> Model:
    """Constroi a definicao formal do Modelo de Tug-of-War para registro no catalogo."""
    p_k_stall = Parameter(
        name="F_s_kinesin",
        description="Forca de parada unitaria da Kinesina-1",
        unit=StandardUnit.PICONEWTON,
        default_value=6.0,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="EVI-VISSCHER-1999-STALL",
        sensitivity_bounds=[5.0, 7.0],
    )
    p_d_stall = Parameter(
        name="F_s_dynein",
        description="Forca de parada unitaria da Dineina Citoplasmatica",
        unit=StandardUnit.PICONEWTON,
        default_value=1.25,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        sensitivity_bounds=[1.0, 2.0],
    )
    p_k_unbinding = Parameter(
        name="epsilon_0_kinesin",
        description="Taxa basal de desprendimento da kinesina",
        unit=StandardUnit.PER_SECOND,
        default_value=1.0,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        sensitivity_bounds=[0.5, 2.0],
    )
    p_d_unbinding = Parameter(
        name="epsilon_0_dynein",
        description="Taxa basal de desprendimento da dineina",
        unit=StandardUnit.PER_SECOND,
        default_value=0.25,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        sensitivity_bounds=[0.1, 0.5],
    )

    return Model(
        id="MOD-TUG-OF-WAR-KINESIN-DYNEIN",
        name="TugOfWar_Bidirectional_Transport",
        description="Modelo estocastico de competicao motora entre equipes de kinesinas e dineinas acopladas a uma mesma vesicula.",
        target_phenomenon="Bidirectional_vesicular_motility",
        assumptions=[
            "Motores da mesma equipe compartilham carga mecanica homogeneamente (equal load sharing).",
            "Taxa de desprendimento segue lei exponencial de Bell: epsilon(F) = epsilon_0 * exp(F / F_d).",
            "A taxa de associacao e proporcional ao numero de motores desacoplados: pi_eff = (N - n) * pi.",
            "O arrasto hidrodinamico e desprezivel frente as forcas de parada de escala em piconewtons geradas pelas equipes.",
        ],
        parameters=[p_k_stall, p_d_stall, p_k_unbinding, p_d_unbinding],
        inputs=["num_kinesins", "num_dyneins", "external_load_pN"],
        outputs=["cargo_velocity_nm_s", "reversal_frequency", "fraction_plus_end", "fraction_minus_end"],
        equations_or_algorithm_description="Equacao Mestra Estocastica dP(n+, n-)/dt com taxas de ligacao pi e desligamento Bell; algoritmo de Gillespie para integracao de Monte Carlo cinetico.",
        implementation_reference="computation.engine.tug_of_war_simulator:run_tug_of_war_simulation",
        source_reference="Muller, Klumpp & Lipowsky (PNAS 2008, DOI: 10.1073/pnas.0706825105)",
        validation_status=ModelValidationStatus.VALIDATED_WITHIN_BOUNDS,
    )
