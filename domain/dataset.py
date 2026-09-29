"""Modelagem de Dataset: colecao curada de dados brutos ou derivados em L2."""

from typing import Any, Dict, List, Optional
from pydantic import Field
from domain.base import BaseDomainModel
from domain.epistemic import DataTier


class Dataset(BaseDomainModel):
    """Colecao curada de dados (RAW ou DERIVED) sob controle estrito de proveniencia."""
    name: str = Field(..., description="Nome identificador do dataset (ex: KIF5B_in_vitro_velocity_data)")
    data_tier: DataTier = Field(..., description="Tier estrito do dataset (RAW ou DERIVED)")
    description: str = Field(...)
    source_ids: List[str] = Field(default_factory=list, description="IDs das Sources de onde o dataset foi derivado ou ingerido")
    storage_uri: str = Field(..., description="Localizacao do arquivo no armazenamento L1")
    checksum_sha256: str = Field(..., description="Hash de integridade dos dados")
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="Esquema das variaveis presentes no dataset")
    record_count: Optional[int] = Field(default=None, ge=0)
