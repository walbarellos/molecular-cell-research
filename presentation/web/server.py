"""Servidor Web da Camada L7 (FastAPI + Dashboard Cientifico Interativo - Ciclo 11).

Oferece endpoints RESTful para simulacao biofisica em tempo real, auditoria
epistemica com Firewall ativo e entrega de interface grafica academica no navegador.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from application.exploration_service import (
    get_system_overview,
    simulate_user_mode,
    get_simulation_curves,
    get_empirical_datasets,
    get_model_catalog,
    get_provenance_graph,
    get_discriminator_matrix,
    get_engineer_view,
    get_scientist_view,
)
from application.simulate_tug_of_war import execute_tug_of_war_cycle
from application.simulate_langevin import execute_langevin_cycle

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="CELL LAB — Scientific Systems Exploration Platform (SSEP)",
    description="Interface visual cientifica/academica de exploracao biofisica e auditoria epistemica.",
    version="1.0.0",
)


# DTOs de requisicao
class KinesinSimRequest(BaseModel):
    atp_uM: float = Field(default=1000.0, ge=0.1, le=5000.0)
    load_pN: float = Field(default=0.0, ge=0.0, le=10.0)
    model_id: str = Field(default="MOD-KIF5B-MINIMAL-MM")


class TugOfWarSimRequest(BaseModel):
    num_kinesins: int = Field(default=4, ge=1, le=15)
    num_dyneins: int = Field(default=4, ge=1, le=15)
    external_load_pN: float = Field(default=0.0, ge=-20.0, le=20.0)
    duration_s: float = Field(default=5.0, ge=0.5, le=30.0)
    seed: Optional[int] = Field(default=42)


class LangevinSimRequest(BaseModel):
    atp_uM: float = Field(default=1000.0, ge=1.0, le=5000.0)
    trap_stiffness_pN_nm: float = Field(default=0.04, ge=0.005, le=0.5)
    total_time_ms: float = Field(default=50.0, ge=10.0, le=250.0)
    dt_us: float = Field(default=2.0, ge=0.1, le=10.0)
    seed: Optional[int] = Field(default=42)


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    overview = get_system_overview()
    return overview.model_dump()


@app.post("/api/simulate/kinesin")
def api_simulate_kinesin(req: KinesinSimRequest) -> Dict[str, Any]:
    user_dto = simulate_user_mode(atp_uM=req.atp_uM, load_pN=req.load_pN, model_id=req.model_id)
    curves = get_simulation_curves(atp_uM=req.atp_uM, load_pN=req.load_pN)
    empirical = get_empirical_datasets()

    return {
        "status": "success",
        "user_state": user_dto.model_dump(),
        "curves": curves,
        "empirical_data": empirical,
    }


@app.post("/api/simulate/tug-of-war")
def api_simulate_tug_of_war(req: TugOfWarSimRequest) -> Dict[str, Any]:
    res = execute_tug_of_war_cycle(
        num_kinesins=req.num_kinesins,
        num_dyneins=req.num_dyneins,
        external_load_pN=req.external_load_pN,
        duration_s=req.duration_s,
        seed=req.seed,
    )
    return res.model_dump()


@app.post("/api/simulate/langevin")
def api_simulate_langevin(req: LangevinSimRequest) -> Dict[str, Any]:
    traj = execute_langevin_cycle(
        atp_uM=req.atp_uM,
        trap_stiffness_pN_nm=req.trap_stiffness_pN_nm,
        total_time_ms=req.total_time_ms,
        dt_us=req.dt_us,
        seed=req.seed,
    )
    return traj.model_dump()


@app.get("/api/provenance")
def api_provenance() -> Dict[str, Any]:
    return get_provenance_graph()


@app.get("/api/models")
def api_models() -> Dict[str, Any]:
    return {"models": get_model_catalog()}


@app.get("/api/discriminator")
def api_discriminator() -> Dict[str, Any]:
    return get_discriminator_matrix()


@app.get("/api/engineer")
def api_engineer() -> Dict[str, Any]:
    eng = get_engineer_view()
    return eng.model_dump()


@app.get("/api/scientist")
def api_scientist() -> Dict[str, Any]:
    sci = get_scientist_view()
    return sci.model_dump()


# Rota principal para entrega da SPA
@app.get("/")
def read_root():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Interface estatica nao encontrada")
    return FileResponse(index_file)


# Montagem dos arquivos estaticos (CSS, JS, SVGs)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
