"""Instanciacao do Modelo Mecanomolecular Minimo KIF5B (Michaelis-Menten 2 Estados)."""

from typing import Optional
from domain import (
    Model,
    Parameter,
    ParameterEpistemicOrigin,
    ModelValidationStatus,
    StandardUnit,
)


def build_kif5b_minimal_model(
    k_cat_default: float = 104.0,
    k_m_default: float = 95.0,
    step_size_default: float = 8.2,
    calibration_evidence_id: Optional[str] = "EVI-SCHNITZER-1997-CALIB",
) -> Model:
    """Constroi o Modelo de 2 Estados Michaelis-Menten com declaracao estrita de premissas e parametros."""

    param_kcat = Parameter(
        name="k_cat",
        description="Taxa catalitica maxima de turnover de ATP por cabeca motora",
        unit=StandardUnit.PER_SECOND,
        default_value=k_cat_default,
        origin=ParameterEpistemicOrigin.MEASURED if calibration_evidence_id else ParameterEpistemicOrigin.ESTIMATED,
        evidence_id=calibration_evidence_id,
        sensitivity_bounds=[80.0, 130.0],
    )

    param_km = Parameter(
        name="K_m",
        description="Constante aparente de Michaelis para ligacao e ativacao de ATP",
        unit=StandardUnit.MICROMOLAR,
        default_value=k_m_default,
        origin=ParameterEpistemicOrigin.MEASURED if calibration_evidence_id else ParameterEpistemicOrigin.ESTIMATED,
        evidence_id=calibration_evidence_id,
        sensitivity_bounds=[60.0, 140.0],
    )

    param_step = Parameter(
        name="step_size",
        description="Deslocamento fisico unitario por ciclo de hidrolise acoplada",
        unit=StandardUnit.NANOMETER,
        default_value=step_size_default,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="EVI-SVOBODA-1993-STEP",
        sensitivity_bounds=[8.0, 8.4],
    )

    model = Model(
        id="MOD-KIF5B-MINIMAL-MM",
        name="KIF5B_Minimal_2State_MichaelisMenten",
        description="Modelo cinetico mecanomolecular minimo que acopla hidrolise irreversivel de ATP a passos discretos de 8.2 nm ao longo do microtúbulo.",
        target_phenomenon="KIF5B_unloaded_velocity_vs_atp",
        assumptions=[
            "Acoplamento estequiometrico estrito: exatamente 1 molecula de ATP e consumida para cada passo mecanico de 8.2 nm.",
            "Deslocamento desimpedido: a forca de carga externa oposta e estritamente nula (F_load = 0.0 pN).",
            "Cinetica de estado estacionario irreversivel: produtos da hidrolise (ADP e Pi) estao em concentracoes baixas o suficiente para impedir reacoes reversas.",
            "Independencia de crowding macromolecular: o ensaio in vitro e assumido purificado em solucao diluida.",
        ],
        parameters=[param_kcat, param_km, param_step],
        inputs=["atp_concentration_uM"],
        outputs=["velocity_um_s"],
        equations_or_algorithm_description="v([ATP]) = (k_cat * [ATP] / (K_m + [ATP])) * (step_size_nm / 1000.0)",
        implementation_reference="computation.formalisms.kinetics:evaluate_michaelis_menten_velocity",
        source_reference="Schnitzer & Block (Nature 1997, DOI: 10.1038/41111)",
        validation_status=ModelValidationStatus.PROVISIONALLY_CONSISTENT,
    )

    return model
