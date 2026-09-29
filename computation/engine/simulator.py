"""Orquestrador de Simulacao e Geracao de Predicoes Cientificas (L5)."""

import hashlib
import json
import platform
import sys
from typing import Dict, List, Optional, Union
import numpy as np

from domain import (
    Model,
    Simulation,
    Prediction,
    Quantity,
    StandardUnit,
    UncertaintyType,
    RepresentationType,
    EpistemicRecord,
    EpistemicStatus,
    DataTier,
    ProvenanceRecord,
    OperatorType,
)
from computation.formalisms.kinetics import (
    evaluate_michaelis_menten_velocity,
    simulate_gillespie_trajectory,
)


def compute_execution_hash(
    model_id: str,
    model_version: str,
    parameters: Dict[str, float],
    inputs: Dict[str, any],
    seed: Optional[int],
) -> str:
    payload = {
        "model_id": model_id,
        "model_version": model_version,
        "parameters": {k: float(v) for k, v in sorted(parameters.items())},
        "inputs": inputs,
        "seed": seed,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_kif5b_simulation(
    model: Model,
    atp_concentrations_uM: Optional[List[float]] = None,
    load_force_pN: float = 0.0,
    conditions: Optional[List[Dict[str, float]]] = None,
    parameter_overrides: Optional[Dict[str, float]] = None,
    mode: str = "analytical",  # "analytical" ou "stochastic_gillespie"
    gillespie_duration_s: float = 5.0,
    random_seed: int = 42,
    dataset_version: Optional[str] = "1.0.0",
) -> Tuple[Simulation, List[Prediction]]:
    """Executa a simulacao do modelo de cinesina gerando registro formal de Simulation e Predicoes."""

    # Normaliza lista de condicoes a simular
    effective_conditions: List[Dict[str, float]] = []
    if conditions is not None:
        effective_conditions = conditions
    elif atp_concentrations_uM is not None:
        effective_conditions = [
            {"atp_concentration_uM": float(atp), "load_force_pN": float(load_force_pN)}
            for atp in atp_concentrations_uM
        ]
    else:
        raise ValueError("Deve ser fornecido 'atp_concentrations_uM' ou 'conditions'.")

    # Parametros efetivos
    params = {p.name: p.default_value for p in model.parameters}
    if parameter_overrides:
        params.update(parameter_overrides)

    k_cat = params["k_cat"]
    k_m = params["K_m"]
    step_size = params["step_size"]

    exec_hash = compute_execution_hash(
        model_id=model.id,
        model_version=model.version,
        parameters=params,
        inputs={"conditions": effective_conditions, "mode": mode},
        seed=random_seed if mode == "stochastic_gillespie" else None,
    )

    env_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
    }

    simulation = Simulation(
        model_id=model.id,
        model_version=model.version,
        dataset_version=dataset_version,
        parameter_overrides=params,
        environment_info=env_info,
        random_seed=random_seed if mode == "stochastic_gillespie" else None,
        execution_hash=exec_hash,
        outputs={},
    )

    predictions: List[Prediction] = []
    simulation_outputs = {"mode": mode, "results": []}

    for cond in effective_conditions:
        atp = float(cond.get("atp_concentration_uM", 0.0))
        load = float(cond.get("load_force_pN", 0.0))

        if mode == "analytical":
            v_pred = evaluate_michaelis_menten_velocity(
                atp_concentration_uM=atp,
                k_cat_per_s=k_cat,
                k_m_uM=k_m,
                step_size_nm=step_size,
            )
            # Incerteza propagada estimada (assumindo 5% de dispersao intrinseca biofisica)
            unc_v = 0.05 * v_pred if v_pred > 0 else 0.001

            pred = Prediction(
                model_id=model.id,
                simulation_id=simulation.id,
                predicted_property="velocity",
                quantity=Quantity(
                    value=round(v_pred, 5),
                    unit=StandardUnit.MICROMETER_PER_SECOND,
                    uncertainty=round(unc_v, 5),
                    uncertainty_type=UncertaintyType.STANDARD_DEVIATION,
                    representation=RepresentationType.POINT_ESTIMATE,
                ),
                conditions={
                    "atp_concentration_uM": atp,
                    "load_force_pN": load,
                },
                epistemic_record=EpistemicRecord(
                    status=EpistemicStatus.PREDICTED,
                    data_tier=DataTier.GENERATED,
                    provenance=ProvenanceRecord(
                        source_uri=f"model:{model.id}",
                        method="analytical_michaelis_menten",
                        operator=OperatorType.MODEL,
                        conditions={"atp_uM": atp, "load_pN": load},
                    ),
                    limitations=[
                        "Predicao gerada sob premissa de forca nula e solucao diluida.",
                        "Nao considera sensibilidade conformacional a forcas contrarias."
                    ],
                    confidence_evidence_count=0,
                ),
            )
            predictions.append(pred)
            simulation_outputs["results"].append({
                "atp_uM": atp,
                "load_pN": load,
                "velocity_um_s": v_pred
            })

        elif mode == "stochastic_gillespie":
            stoch_res = simulate_gillespie_trajectory(
                atp_concentration_uM=atp,
                k_cat_per_s=k_cat,
                k_m_uM=k_m,
                step_size_nm=step_size,
                max_duration_s=gillespie_duration_s,
                random_seed=random_seed,
            )
            v_pred = stoch_res["mean_velocity_um_s"]
            unc_v = 0.08 * v_pred if v_pred > 0 else 0.001

            pred = Prediction(
                model_id=model.id,
                simulation_id=simulation.id,
                predicted_property="velocity",
                quantity=Quantity(
                    value=round(v_pred, 5),
                    unit=StandardUnit.MICROMETER_PER_SECOND,
                    uncertainty=round(unc_v, 5),
                    uncertainty_type=UncertaintyType.STANDARD_DEVIATION,
                    representation=RepresentationType.POINT_ESTIMATE,
                ),
                conditions={
                    "atp_concentration_uM": atp,
                    "load_force_pN": load,
                    "stochastic_steps": stoch_res["total_steps"],
                },
                epistemic_record=EpistemicRecord(
                    status=EpistemicStatus.PREDICTED,
                    data_tier=DataTier.GENERATED,
                    provenance=ProvenanceRecord(
                        source_uri=f"model:{model.id}",
                        method="gillespie_stochastic_stepping",
                        operator=OperatorType.MODEL,
                        conditions={"atp_uM": atp, "load_pN": load, "seed": random_seed},
                    ),
                    limitations=["Simulacao estocastica finita de passos discretos."],
                    confidence_evidence_count=0,
                ),
            )
            predictions.append(pred)
            simulation_outputs["results"].append({
                "atp_uM": atp,
                "load_pN": load,
                "velocity_um_s": v_pred,
                "total_steps": stoch_res["total_steps"],
            })

    simulation.outputs = simulation_outputs
    simulation.predictions = predictions

    return simulation, predictions

