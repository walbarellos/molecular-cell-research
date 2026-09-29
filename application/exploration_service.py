"""Servico de Aplicacao para Exploracao Cientifica nos 3 Niveis de Zoom (L6 -> L7).

Fornece abstracao de acesso a dados epistemica, modelos biofisicos (M1 a M4)
e interfaces para a visualizacao Web e CLI.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from domain import (
    Observation,
    EvidenceRecord,
    Claim,
    ConflictRecord,
)
from computation.models.kinesin_minimal import build_kif5b_minimal_model
from computation.models.kinesin_force_dependent import (
    build_kif5b_force_dependent_model,
    KinesinForceDependentModel,
    evaluate_force_dependent_velocity,
)
from computation.models.tug_of_war import build_tug_of_war_model
from computation.models.langevin_model import build_langevin_model
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
    """Retorna visao macroscopica de estado de conhecimento do sistema."""
    total_evidences = 21
    total_obs = 21
    total_sources = 2
    total_experiments = 2
    total_claims = 2
    val_claims = 1
    contra_claims = 1
    total_conflicts = 1
    total_models = 4  # M1, M2, M3 (Tug-of-War), M4 (Langevin)

    return SystemOverviewDTO(
        phenomenon="CELL-LAB-001 (KIF5B Motility on Microtubule)",
        total_sources=total_sources,
        total_experiments=total_experiments,
        total_observations=total_obs,
        total_evidences=total_evidences,
        total_claims=total_claims,
        validated_claims=val_claims,
        contradicted_claims=contra_claims,
        total_models=total_models,
        total_conflicts=total_conflicts,
    )


def simulate_user_mode(
    atp_uM: float = 1000.0,
    load_pN: float = 0.0,
    model_id: str = "MOD-KIF5B-MINIMAL-MM",
) -> UserViewDTO:
    """Simula operacao pontual de motor unico com inspecao de Firewall Epistemico."""
    is_m2 = model_id.upper() in ("M2", "MOD-KIF5B-4STATE-FORCE-DEPENDENT")

    if is_m2:
        m2 = KinesinForceDependentModel()
        vel = m2.predict_velocity(atp_uM=atp_uM, load_pN=load_pN)
        unc = 0.035 if load_pN > 0 else 0.04
        is_valid_envelope = (0.0 <= load_pN <= 6.0 and 2.0 <= atp_uM <= 2000.0)
        warning = None
        if not is_valid_envelope:
            warning = f"AVISO: Condicoes ([ATP]={atp_uM} uM, F={load_pN} pN) extrapolam o envelope validado do Modelo M2."
    else:
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

        # Avalia envelope de validacao do M1
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


def get_empirical_datasets() -> Dict[str, Any]:
    """Retorna os dados empiricos calibrados dos Datasets A e B com incertezas."""
    derived_dir = _get_derived_dir()
    dts_a_file = derived_dir / "dataset_a_calibration.json"
    dts_b_file = derived_dir / "dataset_b_falsification.json"

    dataset_a_points = []
    if dts_a_file.exists():
        with open(dts_a_file, "r", encoding="utf-8") as f:
            data_a = json.load(f)
            for obs in data_a.get("observations", []):
                params = obs.get("contextual_parameters", {})
                atp = params.get("atp_concentration_uM")
                obs_val = obs.get("observed_value", {})
                val = obs_val.get("value")
                unc = obs_val.get("uncertainty")
                if atp is not None and val is not None:
                    dataset_a_points.append({
                        "atp_uM": atp,
                        "velocity_um_s": val,
                        "uncertainty_um_s": unc or 0.04,
                        "load_force_pN": 0.0,
                    })

    dataset_b_points = []
    if dts_b_file.exists():
        with open(dts_b_file, "r", encoding="utf-8") as f:
            data_b = json.load(f)
            for obs in data_b.get("observations", []):
                params = obs.get("contextual_parameters", {})
                load_f = params.get("load_force_pN")
                atp = params.get("atp_concentration_uM", 1000.0)
                obs_val = obs.get("observed_value", {})
                val = obs_val.get("value")
                unc = obs_val.get("uncertainty")
                if load_f is not None and val is not None:
                    dataset_b_points.append({
                        "load_force_pN": load_f,
                        "atp_uM": atp,
                        "velocity_um_s": val,
                        "uncertainty_um_s": unc or 0.03,
                    })

    return {
        "dataset_a": dataset_a_points,
        "dataset_b": dataset_b_points,
    }


def get_simulation_curves(atp_uM: float = 1000.0, load_pN: float = 0.0) -> Dict[str, Any]:
    """Gera curvas analiticas para traco no dashboard (Michaelis-Menten e Forca-Velocidade)."""
    # 1. Curva Forca-Velocidade v(F) sob [ATP] atual (F de 0 a 7 pN)
    f_grid = np.linspace(0.0, 7.0, 71)
    fv_m1 = []
    fv_m2 = []

    m1_base = build_kif5b_minimal_model()
    k_cat_m1 = 103.92
    km_m1 = 94.63
    step_nm = 8.2
    v_m1_fixed = ((k_cat_m1 * atp_uM) / (km_m1 + atp_uM)) * (step_nm / 1000.0)

    for f_val in f_grid:
        # M1 e cego a forca (quimioestatico)
        fv_m1.append({"load_pN": round(float(f_val), 2), "velocity_um_s": round(float(v_m1_fixed), 4)})
        # M2 possui acoplamento mecanoquimico Bell/Kramers
        v_m2_val = evaluate_force_dependent_velocity(atp_concentration_uM=atp_uM, load_force_pN=f_val)
        fv_m2.append({"load_pN": round(float(f_val), 2), "velocity_um_s": round(float(v_m2_val), 4)})

    # 2. Curva Michaelis-Menten v([ATP]) sob F atual (ATP de 0 a 2000 uM)
    atp_grid = np.geomspace(1.0, 2500.0, 60)
    mm_m1 = []
    mm_m2 = []

    for a_val in atp_grid:
        v_m1 = ((k_cat_m1 * a_val) / (km_m1 + a_val)) * (step_nm / 1000.0)
        mm_m1.append({"atp_uM": round(float(a_val), 1), "velocity_um_s": round(float(v_m1), 4)})

        v_m2 = evaluate_force_dependent_velocity(atp_concentration_uM=a_val, load_force_pN=load_pN)
        mm_m2.append({"atp_uM": round(float(a_val), 1), "velocity_um_s": round(float(v_m2), 4)})

    # Ponto operacional atual
    v_oper_m1 = v_m1_fixed
    v_oper_m2 = evaluate_force_dependent_velocity(atp_concentration_uM=atp_uM, load_force_pN=load_pN)

    is_m1_valid = (load_pN == 0.0 and 2.0 <= atp_uM <= 2000.0)
    is_m2_valid = (0.0 <= load_pN <= 6.0 and 2.0 <= atp_uM <= 2000.0)

    return {
        "operating_point": {
            "atp_uM": atp_uM,
            "load_pN": load_pN,
            "velocity_m1_um_s": round(float(v_oper_m1), 4),
            "velocity_m2_um_s": round(float(v_oper_m2), 4),
            "m1_valid": is_m1_valid,
            "m2_valid": is_m2_valid,
            "stall_force_pN": 6.13,
        },
        "force_velocity_curve": {
            "m1": fv_m1,
            "m2": fv_m2,
        },
        "michaelis_menten_curve": {
            "m1": mm_m1,
            "m2": mm_m2,
        },
    }


def get_model_catalog() -> List[Dict[str, Any]]:
    """Retorna o catalogo com os 4 modelos registrados na plataforma."""
    m1 = build_kif5b_minimal_model()
    m2 = build_kif5b_force_dependent_model()
    m3 = build_tug_of_war_model()
    m4 = build_langevin_model()

    models = [m1, m2, m3, m4]
    catalog = []
    for m in models:
        catalog.append({
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "target_phenomenon": m.target_phenomenon,
            "assumptions": m.assumptions,
            "validation_status": m.validation_status.value if hasattr(m.validation_status, "value") else str(m.validation_status),
            "source_reference": m.source_reference,
            "equations_or_algorithm": m.equations_or_algorithm_description,
            "parameters": [
                {
                    "name": p.name,
                    "description": p.description,
                    "unit": p.unit.value if hasattr(p.unit, "value") else str(p.unit),
                    "default_value": p.default_value,
                    "origin": p.origin.value if hasattr(p.origin, "value") else str(p.origin),
                }
                for p in m.parameters
            ],
        })
    return catalog


def get_provenance_graph() -> Dict[str, Any]:
    """Retorna dados de nós e arestas para renderizacao interativa do Grafo Epistemico."""
    nodes = [
        {"id": "SRC-SCHNITZER-1997", "label": "Schnitzer & Block (Nature 1997)", "type": "SOURCE", "tier": "RAW"},
        {"id": "SRC-VISSCHER-1999", "label": "Visscher et al. (Nature 1999)", "type": "SOURCE", "tier": "RAW"},
        {"id": "EXP-SCHNITZER-1997", "label": "Optical Trap Motility (Load=0)", "type": "EXPERIMENT", "tier": "RAW"},
        {"id": "EXP-VISSCHER-1999", "label": "Molecular Force Clamp", "type": "EXPERIMENT", "tier": "RAW"},
        {"id": "DTS-CALIBRATION-A", "label": "Dataset A (Calibracao [ATP])", "type": "DATASET", "tier": "RAW"},
        {"id": "DTS-FALSIFICATION-B", "label": "Dataset B (Forca vs Velocidade)", "type": "DATASET", "tier": "RAW"},
        {"id": "MOD-KIF5B-MINIMAL-MM", "label": "M1: KIF5B Minimal MM (Quimioestatico)", "type": "MODEL", "tier": "DERIVED", "status": "FALSIFIED_UNDER_LOAD"},
        {"id": "CLM-KIF5B-REPRODUCTION-001", "label": "CLM-001: M1 Valido em Carga Nula", "type": "CLAIM", "tier": "DERIVED", "status": "VALIDATED"},
        {"id": "CLM-KIF5B-FALSIFICATION-001", "label": "CLM-002: M1 Refutado sob Carga", "type": "CLAIM", "tier": "DERIVED", "status": "FALSIFIED"},
        {"id": "CONF-KIF5B-LOAD-001", "label": "CONF-001: Falha Quimioestatica (z=-49.8)", "type": "CONFLICT", "tier": "DERIVED", "status": "RESOLVED_BY_M2"},
        {"id": "HYP-KRAMERS-001", "label": "HYP-001: Acoplamento Mecanoquimico Bell/Kramers", "type": "HYPOTHESIS", "tier": "DERIVED", "status": "CONFIRMED"},
        {"id": "MOD-KIF5B-4STATE-FORCE-DEPENDENT", "label": "M2: 4-State Bell/Kramers Force-Dependent", "type": "MODEL", "tier": "DERIVED", "status": "VALIDATED"},
        {"id": "MOD-TUG-OF-WAR", "label": "M3: Tug-of-War Kinesin vs Dynein", "type": "MODEL", "tier": "DERIVED", "status": "ACTIVE"},
        {"id": "MOD-LANGEVIN", "label": "M4: Langevin Estocastico (Ruido Termico)", "type": "MODEL", "tier": "DERIVED", "status": "ACTIVE"},
    ]

    edges = [
        {"from": "SRC-SCHNITZER-1997", "to": "EXP-SCHNITZER-1997", "relation": "DESCRIBES"},
        {"from": "SRC-VISSCHER-1999", "to": "EXP-VISSCHER-1999", "relation": "DESCRIBES"},
        {"from": "EXP-SCHNITZER-1997", "to": "DTS-CALIBRATION-A", "relation": "PRODUCES"},
        {"from": "EXP-VISSCHER-1999", "to": "DTS-FALSIFICATION-B", "relation": "PRODUCES"},
        {"from": "DTS-CALIBRATION-A", "to": "MOD-KIF5B-MINIMAL-MM", "relation": "CALIBRATES"},
        {"from": "MOD-KIF5B-MINIMAL-MM", "to": "CLM-KIF5B-REPRODUCTION-001", "relation": "PREDICTS"},
        {"from": "DTS-CALIBRATION-A", "to": "CLM-KIF5B-REPRODUCTION-001", "relation": "SUPPORTS"},
        {"from": "DTS-FALSIFICATION-B", "to": "CLM-KIF5B-FALSIFICATION-001", "relation": "REFUTES_PREDICTION"},
        {"from": "CLM-KIF5B-FALSIFICATION-001", "to": "CONF-KIF5B-LOAD-001", "relation": "TRIGGERS"},
        {"from": "CONF-KIF5B-LOAD-001", "to": "HYP-KRAMERS-001", "relation": "MOTIVATES"},
        {"from": "HYP-KRAMERS-001", "to": "MOD-KIF5B-4STATE-FORCE-DEPENDENT", "relation": "FORMALIZED_IN"},
        {"from": "DTS-CALIBRATION-A", "to": "MOD-KIF5B-4STATE-FORCE-DEPENDENT", "relation": "VALIDATES"},
        {"from": "DTS-FALSIFICATION-B", "to": "MOD-KIF5B-4STATE-FORCE-DEPENDENT", "relation": "VALIDATES"},
        {"from": "MOD-KIF5B-4STATE-FORCE-DEPENDENT", "to": "CONF-KIF5B-LOAD-001", "relation": "RESOLVES"},
        {"from": "MOD-KIF5B-4STATE-FORCE-DEPENDENT", "to": "MOD-TUG-OF-WAR", "relation": "EXTENDS_TO_TEAMS"},
        {"from": "MOD-KIF5B-4STATE-FORCE-DEPENDENT", "to": "MOD-LANGEVIN", "relation": "DRIVES_STEPPING"},
    ]

    return {"nodes": nodes, "edges": edges}


def get_discriminator_matrix() -> Dict[str, Any]:
    """Retorna dados do ensaio discriminatorio otimo e matriz de sensibilidade."""
    derived_dir = _get_derived_dir()
    design_file = derived_dir / "experiment_design_cell_lab_001.json"
    if design_file.exists():
        with open(design_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    return {}


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
