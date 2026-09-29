"""Modelo Formal da Dinamica de Langevin Estocastica com Pinca Optica (Ciclo 13)."""

from domain.model import (
    Model,
    Parameter,
    ParameterEpistemicOrigin,
    ModelValidationStatus,
)
from domain.units import StandardUnit


def build_langevin_model() -> Model:
    """Constroi a definicao formal do Modelo de Langevin Estocastico."""
    p_k_trap = Parameter(
        name="trap_stiffness",
        description="Rigidez elastica do poco optico da pinca optica",
        unit=StandardUnit.PICONEWTON,
        default_value=0.04,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="EVI-SVOBODA-1993-TRAP",
        sensitivity_bounds=[0.01, 0.20],
    )
    p_radius = Parameter(
        name="bead_radius",
        description="Raio hidrodinamico da microesfera de poliestireno",
        unit=StandardUnit.NANOMETER,
        default_value=250.0,
        origin=ParameterEpistemicOrigin.MEASURED,
        sensitivity_bounds=[100.0, 500.0],
    )
    p_step = Parameter(
        name="step_size",
        description="Passo mecanico unitario discreto da kinesina",
        unit=StandardUnit.NANOMETER,
        default_value=8.2,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id="EVI-SVOBODA-1993-STEP",
        sensitivity_bounds=[8.0, 8.4],
    )
    p_gamma = Parameter(
        name="stokes_drag_gamma",
        description="Coeficiente de arrasto viscoso Stokes da esfera",
        unit=StandardUnit.DIMENSIONLESS,
        default_value=0.004712,
        origin=ParameterEpistemicOrigin.ESTIMATED,
        sensitivity_bounds=[0.002, 0.010],
    )

    return Model(
        id="MOD-LANGEVIN-STOCHASTIC-STEPPING",
        name="Langevin_Overdamped_Optical_Trap_Stepping",
        description="Integrador estocastico continuo em microsegundos da equacao de Langevin acoplada a pinca optica e transicoes mecanoquimicas discretas de 8.2 nm.",
        target_phenomenon="Single_molecule_optical_trap_stepping_traces",
        assumptions=[
            "Limite sobreamortecido de baixo Reynolds (Re << 10^-4): inercia da esfera e desprezivel.",
            "Ruido termico satisfaz o teorema de flutuacao-dissipacao de Einstein: <xi(t)xi(t')> = 2*k_B*T*gamma*delta(t-t').",
            "Poco da pinca optica e harmonico na regiao linear de deflexao do laser: U_trap = 0.5 * kappa * (x - x_trap)^2.",
            "O acoplamento elastico entre cabeca do motor e esfera segue rigidez de linker k_linker.",
            "Taxa de transicao mecanoquimica do motor obedece a cinetica mecanoquimica M2 Kramers sob a forca restauradora instantanea da pinca.",
        ],
        parameters=[p_k_trap, p_radius, p_step, p_gamma],
        inputs=["atp_concentration_uM", "trap_stiffness_pN_nm", "total_time_ms", "dt_us"],
        outputs=["bead_trajectory_nm", "step_events", "stall_force_pN", "thermal_rms_nm"],
        equations_or_algorithm_description="gamma * dx/dt = -kappa_trap*(x - x_trap) - k_linker*(x - x_motor) + sqrt(2*k_B*T*gamma)*xi(t); solucao exata de Ornstein-Uhlenbeck com saltos Poissonianos k_cat(F).",
        implementation_reference="computation.engine.langevin_simulator:run_langevin_simulation",
        source_reference="Svoboda, Schmidt, Schnitzer, Block (Nature 1993, DOI: 10.1038/365721a0)",
        validation_status=ModelValidationStatus.VALIDATED_WITHIN_BOUNDS,
    )
