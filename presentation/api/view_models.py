"""DTOs e ViewModels da Camada L7 com garantia de Firewall Epistemico."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SystemOverviewDTO(BaseModel):
    """Visao macroscopica de estado de conhecimento do sistema."""
    model_config = ConfigDict(frozen=True)

    phenomenon: str
    total_sources: int
    total_experiments: int
    total_observations: int
    total_evidences: int
    total_claims: int
    validated_claims: int
    contradicted_claims: int
    total_models: int
    total_conflicts: int


class UserViewDTO(BaseModel):
    """ViewModel para o Modo Usuario (Simulacao e exploracao funcional direta)."""
    model_config = ConfigDict(frozen=True)

    atp_concentration_uM: float
    load_force_pN: float
    predicted_velocity_um_s: float
    predicted_uncertainty_um_s: float
    operational_state: str  # ex: "Saturating ATP / Steady-state motility"
    data_tier: str = Field(default="GENERATED", description="Firewall Epistemico: Tier de dados")
    epistemic_status: str = Field(default="PREDICTED", description="Firewall Epistemico: Status epistemico")
    is_within_validated_envelope: bool
    epistemic_warning: Optional[str] = None


class EngineerViewDTO(BaseModel):
    """ViewModel para o Modo Engenheiro (Entidades, componentes, parametros operacionais)."""
    model_config = ConfigDict(frozen=True)

    entities: List[Dict[str, Any]]
    model_name: str
    parameters: List[Dict[str, Any]]
    operating_envelope: Dict[str, Any]
    supporting_evidence_count: int


class ScientistViewDTO(BaseModel):
    """ViewModel para o Modo Cientifico (Caixa-preta aberta, proveniencia e contradicoes)."""
    model_config = ConfigDict(frozen=True)

    active_model_id: str
    assumptions: List[str]
    provenance_chain: Dict[str, Any]
    active_claims: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
