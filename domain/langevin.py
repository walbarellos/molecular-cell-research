"""Modelagem de Dominio para Dinâmica Estocastica de Langevin com Ruído Termico (Ciclo 13).

Simulacao em microsegundos da trajetoria da carga acoplada ao poco de potencial
optico e a rede periodica de tubulina com transicoes mecanoquimicas discretas de 8.2 nm.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LangevinConfig(BaseModel):
    """Parametros fisicos e numericos para integracao de Langevin sobreamortecida."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_time_ms: float = Field(default=50.0, gt=0.0, le=500.0, description="Tempo total de integracao em milissegundos")
    dt_us: float = Field(default=2.0, gt=0.05, le=20.0, description="Passo temporal de integracao Euler-Maruyama em microsegundos")
    atp_concentration_uM: float = Field(default=1000.0, gt=0.0, description="Concentracao de ATP em uM")
    bead_radius_nm: float = Field(default=250.0, gt=10.0, description="Raio hidrodinamico do bead de poliestireno em nm")
    viscosity_Pa_s: float = Field(default=0.001, gt=0.0, description="Viscosidade dinâmica do meio aquoso em Pa*s")
    temperature_degC: float = Field(default=24.0, ge=0.0, le=60.0, description="Temperatura experimental em graus Celsius")
    trap_stiffness_pN_nm: float = Field(default=0.04, ge=0.0, le=0.5, description="Constante elastica da pinca optica kappa em pN/nm")
    trap_center_nm: float = Field(default=0.0, description="Posicao de equilibrio do poco harmonico da pinca optica em nm")
    step_size_nm: float = Field(default=8.2, gt=0.0, description="Passo elementar de transicao mecanica do motor em nm")
    random_seed: Optional[int] = Field(default=None, description="Semente aleatoria para repetibilidade")


class LangevinPoint(BaseModel):
    """Ponto amostrado da trajetoria temporal estocastica."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    time_ms: float = Field(..., ge=0.0)
    bead_position_nm: float = Field(...)
    motor_position_nm: float = Field(...)
    trap_force_pN: float = Field(...)
    step_count: int = Field(..., ge=0)


class LangevinStepMetrics(BaseModel):
    """Metricas biofisicas extraidas da trajetoria estocastica de Langevin."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_steps: int = Field(..., ge=0)
    mean_velocity_nm_s: float
    stall_force_reached_pN: float
    thermal_noise_rms_nm: float = Field(..., ge=0.0, description="Flutuacao termica rms sqrt(<(x - <x>)^2>)")
    drag_coefficient_pN_us_nm: float = Field(..., gt=0.0, description="Coeficiente de atrito de Stokes gamma")
    diffusion_coefficient_nm2_us: float = Field(..., gt=0.0, description="Constante de difusao Einstein-Smoluchowski D = k_B*T / gamma")


class LangevinTrajectory(BaseModel):
    """Trajetoria estocastica completa amostrada com metadados experimentais."""
    model_config = ConfigDict(frozen=True)

    config: LangevinConfig
    metrics: LangevinStepMetrics
    points: List[LangevinPoint]
    histogram_bins: List[float] = Field(default_factory=list)
    histogram_counts: List[int] = Field(default_factory=list)
