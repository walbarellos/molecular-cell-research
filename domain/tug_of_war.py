"""Modelagem de Dominio para Competição Motora (Tug-of-War Kinesin vs. Dynein - Ciclo 12).

Baseado no formalismo biofisico de Muller, Klumpp & Lipowsky (PNAS 2008 / Biophys J 2008).
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from domain.base import BaseDomainModel
from domain.units import StandardUnit
from domain.measurement import Quantity


class MotorDirection(str, Enum):
    PLUS_END = "plus_end"    # Anterogrado / Kinesina
    MINUS_END = "minus_end"  # Retrogrado / Dineina


class MotorSpeciesSpec(BaseModel):
    """Especificacao quantitativa e parâmetros cineticos de uma especie motora."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., description="Nome da especie motora (ex: Kinesin-1, Cytoplasmic Dynein)")
    direction: MotorDirection = Field(...)
    stall_force_pN: float = Field(..., gt=0.0, description="Forca de parada unitaria F_s em pN")
    detachment_force_pN: float = Field(..., gt=0.0, description="Forca caracteristica de desprendimento F_d em pN")
    unloaded_velocity_nm_s: float = Field(..., description="Velocidade sem carga v_0 em nm/s")
    unbinding_rate_0_per_s: float = Field(..., gt=0.0, description="Taxa de desprendimento espontaneo epsilon_0 em s^-1")
    binding_rate_per_s: float = Field(..., gt=0.0, description="Taxa de ligacao por motor disponivel pi em s^-1")
    step_size_nm: float = Field(default=8.2, gt=0.0, description="Tamanho do passo elementar em nm")


class TugOfWarConfig(BaseModel):
    """Configuracao de uma simulacao de competicao motora vesicular."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    num_kinesins: int = Field(default=4, ge=1, le=20, description="Numero total de kinesinas acopladas a carga (N_+)")
    num_dyneins: int = Field(default=4, ge=1, le=20, description="Numero total de dineinas acopladas a carga (N_-)")
    kinesin_spec: Optional[MotorSpeciesSpec] = Field(default=None)
    dynein_spec: Optional[MotorSpeciesSpec] = Field(default=None)
    external_load_pN: float = Field(default=0.0, description="Forca externa aplicada a carga F_ext em pN")
    simulation_duration_s: float = Field(default=5.0, gt=0.0, le=60.0, description="Tempo maximo de simulacao em segundos")
    random_seed: Optional[int] = Field(default=None, description="Semente pseudoaleatoria para reprodutibilidade estocastica")


class TugOfWarState(BaseModel):
    """Estado estocastico instantaneo do complexo vesicular."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    time_s: float = Field(..., ge=0.0)
    bound_kinesins: int = Field(..., ge=0)
    bound_dyneins: int = Field(..., ge=0)
    cargo_velocity_nm_s: float = Field(...)
    cargo_position_nm: float = Field(...)
    tension_force_pN: float = Field(..., ge=0.0, description="Tensao mecanica interna entre equipes de motores")
    state_classification: str = Field(..., description="PLUS_END_MOTION | MINUS_END_MOTION | TUG_OF_WAR_PAUSE | UNBOUND")


class TugOfWarMetrics(BaseModel):
    """Metricas quantitativas agregadas de uma trajetoria estocastica."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    total_time_s: float
    total_distance_nm: float
    net_velocity_nm_s: float
    fraction_plus_end: float = Field(..., ge=0.0, le=1.0)
    fraction_minus_end: float = Field(..., ge=0.0, le=1.0)
    fraction_pause_tug_of_war: float = Field(..., ge=0.0, le=1.0)
    fraction_unbound: float = Field(..., ge=0.0, le=1.0)
    directional_reversals: int = Field(..., ge=0)
    mean_kinesins_engaged: float = Field(..., ge=0.0)
    mean_dyneins_engaged: float = Field(..., ge=0.0)


class TugOfWarSimulationResult(BaseModel):
    """Resultado completo da simulacao estocastica de Tug-of-War."""
    model_config = ConfigDict(frozen=True)

    config: TugOfWarConfig
    metrics: TugOfWarMetrics
    trajectory: List[TugOfWarState]
    steady_state_distribution: Dict[str, float] = Field(
        default_factory=dict,
        description="Distribuicao estacionaria da equacao mestra: P(n_+, n_-)"
    )
