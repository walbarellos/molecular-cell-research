"""Modelagem de Execucao de Simulacoes computacionais e Predicoes resultantes."""

from typing import Any, Dict, List, Optional
from pydantic import Field, model_validator
from domain.base import BaseDomainModel
from domain.epistemic import EpistemicRecord, EpistemicStatus, DataTier
from domain.measurement import Quantity


class Prediction(BaseDomainModel):
    """Declaracao antecipada de medicao gerada por um modelo antes de confronto empirico."""
    model_id: str = Field(..., description="ID do Model que gerou esta predicao")
    simulation_id: str = Field(..., description="ID da Simulation executada")
    predicted_property: str = Field(..., description="Nome da grandeza predita (ex: velocity)")
    quantity: Quantity = Field(..., description="Valor quantitativo, unidade e incerteza computada")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Condicoes simuladas (ex: ATP=1.0 mM, load=0.0 pN)")
    epistemic_record: EpistemicRecord = Field(...)

    @model_validator(mode="after")
    def validate_prediction_invariants(self) -> "Prediction":
        # INV-PREDICTION-001: Uma Prediction deve indicar qual modelo a produziu
        if not self.model_id or not self.model_id.strip():
            raise ValueError("INV-PREDICTION-001: Prediction deve referenciar um model_id valido.")
        if not self.simulation_id or not self.simulation_id.strip():
            raise ValueError("INV-PREDICTION-001: Prediction deve referenciar uma simulation_id valida.")
        # Predicoes sao por definicao GENERATED e com status PREDICTED ou MODELED
        if self.epistemic_record.data_tier != DataTier.GENERATED:
            raise ValueError("Invariante de integridade: Prediction deve pertencer ao data_tier GENERATED.")
        if self.epistemic_record.status not in (EpistemicStatus.PREDICTED, EpistemicStatus.MODELED):
            raise ValueError(f"Invariante de integridade: Prediction nao pode ter status {self.epistemic_record.status}.")
        return self


class Simulation(BaseDomainModel):
    """Registro de execucao deterministica ou estocastica de um modelo (Reprodutibilidade)."""
    model_id: str = Field(..., description="ID do modelo executado")
    model_version: str = Field(...)
    dataset_version: Optional[str] = Field(default=None, description="Versao do dataset de calibracao utilizado, se aplicavel")
    parameter_overrides: Dict[str, float] = Field(default_factory=dict)
    environment_info: Dict[str, str] = Field(
        default_factory=dict,
        description="OS, versao de Python, bibliotecas numericas e arquitetura de CPU"
    )
    random_seed: Optional[int] = Field(default=None, description="Semente pseudoaleatoria para garantir determinismo")
    execution_hash: str = Field(..., description="Hash SHA-256 dos parametros de entrada e configuracao")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="Sumario estatistico das saidas geradas")
    predictions: List[Prediction] = Field(default_factory=list, description="Predicoes extraidas desta execucao")

    @model_validator(mode="after")
    def validate_simulation_reproducibility(self) -> "Simulation":
        # INV-REPRO-001: Uma execucao deve registrar versoes e hash de execucao
        if not self.model_version or not self.model_version.strip():
            raise ValueError("INV-REPRO-001: Simulation exige model_version definida.")
        if not self.execution_hash or not self.execution_hash.strip():
            raise ValueError("INV-REPRO-001: Simulation exige execution_hash para auditabilidade.")
        return self
