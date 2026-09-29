"""Servico de Aplicacao para Exploraçao Cientifica nos 3 Niveis de Zoom (L6 -> L7)."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain import (
    Observation,
    EvidenceRecord,
    Claim,
    ConflictRecord,
)
from computation.models.kinesin_minimal import build_kif5b_minimal_model
from computation.engine.simulator import run_kif5b_simulation
from presentation.api.view_models import (
    SystemOverviewDTO,
    UserViewDTO,
    EngineerViewDTO,
    ScientistViewDTO,
)


def _get_derived_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "derived" / "cell_lab_001"


def get_system_overview() -> SystemOverviewDTO:
    derived_dir = _get_derived_dir()
    manifest_file = derived_dir / "manifest_cell_lab_001.json"
    repro_file = derived_dir / "reproduction_report_dataset_a.json"
    falsif_file = derived_dir / "falsification_report_dataset_b.json"

    total_evidences = 21
    total_obs = 21
    total_sources = 2
    total_experiments = 2
    total_claims = 2
    val_claims = 1
    contra_claims = 1
    total_conflicts = 1

    return SystemOverviewDTO(
        phenomenon="CELL-LAB-001 (KIF5B Motility on Microtubule)",
        total_sources=total_sources,
        total_experiments=total_experiments,
        total_observations=total_obs,
        total_evidences=total_evidences,
        total_claims=total_claims,
        validated_claims=val_claims,
        contradicted_claims=contra_claims,
        total_models=1,
        total_conflicts=total_conflicts,
    )


def simulate_user_mode(atp_uM: float = 1000.0, load_pN: float = 0.0) -> UserViewDTO:
    model = build_kif5b_minimal_model(k_cat_default=103.92, k_m_default=94.63, step_size_default=8.2)

    simulation, predictions = run_kif5b_simulation(
        model=model,
        atp_concentrations_uM=[atp_uM],
        load_force_pN=load_pN,
        mode="analytical",
    )
    pred = predictions[0]
    vel = pred.quantity.value
    unc = pred.quantity.uncertainty or 0.04

    # Avalia envelope de validacao
    is_valid_envelope = (load_pN == 0.0 and 2.0 <= atp_uM <= 2000.0)
    warning = None

    if load_pN > 0.0:
        warning = (
            f"ALERTA EPISTEMICO: Regime sob carga contraria (F = {load_pN} pN) foi EMPIRICAMENTE REFUTADO "
            "pelo Dataset B (ver CONFLICT CONF-KIF5B-LOAD-001). A velocidade real esperada e muito inferior a calculada."
        )
    elif atp_uM < 2.0 or atp_uM > 2000.0:
        warning = f"AVISO: Concentracao de ATP ({atp_uM} uM) extrapola a faixa empiricamente validada [2.0, 2000.0] uM."

    state = "Saturating ATP Motility" if atp_uM >= 500 else ("Sub-saturating Stepping" if atp_uM >= 50 else "Limiting ATP Kinetics")

    return UserViewDTO(
        atp_concentration_uM=atp_uM,
        load_force_pN=load_pN,
        predicted_velocity_um_s=vel,
        predicted_uncertainty_um_s=unc,
        operational_state=state,
        data_tier="GENERATED",
        epistemic_status="PREDICTED",
        is_within_validated_envelope=is_valid_envelope,
        epistemic_warning=warning,
    )


def get_engineer_view() -> EngineerViewDTO:
    derived_dir = _get_derived_dir()
    manifest_file = derived_dir / "manifest_cell_lab_001.json"
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    entities = [
        manifest["entities"]["kinesin"],
        manifest["entities"]["microtubule"],
    ]

    model = build_kif5b_minimal_model(k_cat_default=103.92, k_m_default=94.63, step_size_default=8.2)

    params = [
        {
            "name": p.name,
            "description": p.description,
            "unit": p.unit,
            "calibrated_value": p.default_value,
            "origin": p.origin,
            "sensitivity_bounds": p.sensitivity_bounds,
        }
        for p in model.parameters
    ]

    envelope = {
        "validated_atp_range_uM": [2.0, 2000.0],
        "validated_load_force_pN": 0.0,
        "temperature_degC": 24.0,
        "buffer": "BRB80",
        "stall_force_empiric_pN": 6.0,
    }

    return EngineerViewDTO(
        entities=entities,
        model_name=model.name,
        parameters=params,
        operating_envelope=envelope,
        supporting_evidence_count=10,
    )


def get_scientist_view() -> ScientistViewDTO:
    derived_dir = _get_derived_dir()
    repro_file = derived_dir / "reproduction_report_dataset_a.json"
    falsif_file = derived_dir / "falsification_report_dataset_b.json"

    with open(repro_file, "r", encoding="utf-8") as f:
        repro_data = json.load(f)

    with open(falsif_file, "r", encoding="utf-8") as f:
        falsif_data = json.load(f)

    model = build_kif5b_minimal_model(k_cat_default=103.92, k_m_default=94.63)

    chain = {
        "source": "Schnitzer & Block (Nature 1997, DOI: 10.1038/41111)",
        "experiment": "EXP-SCHNITZER-1997-MOTILITY (Optical Trap Motility)",
        "sample_observation": "OBS-A-008: 0.814 um/s at 1000 uM ATP (load = 0 pN)",
        "evidence": "EVI-A-008 (RAW / OBSERVED)",
        "claim": repro_data["validation_claim"]["id"],
        "model": model.id,
        "simulation": repro_data["simulation_id"],
        "prediction_sample": "PRED: 0.778 um/s at 1000 uM ATP",
    }

    claims = [
        repro_data["validation_claim"],
        falsif_data["falsification_claim"],
    ]

    conflicts = [
        falsif_data["conflict_record"]
    ]

    return ScientistViewDTO(
        active_model_id=model.id,
        assumptions=model.assumptions,
        provenance_chain=chain,
        active_claims=claims,
        conflicts=conflicts,
    )
