"""Pipeline de Orquestracao de Confronto Epistemico e Deteccao de Falhas sobre Dataset B (Ciclo 07)."""

import json
from pathlib import Path
import sys
from typing import Dict, Any

# Garante path do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain import (
    Observation,
    EvidenceRecord,
    Claim,
    ConflictRecord,
    ConflictResolutionStatus,
    EpistemicRecord,
    EpistemicStatus,
    DataTier,
)
from computation.models.kinesin_minimal import build_kif5b_minimal_model
from computation.engine.simulator import run_kif5b_simulation
from analysis.comparator import compare_observations_and_predictions, ComparisonReport


def execute_dataset_b_falsification() -> Dict[str, Any]:
    project_root = Path(__file__).resolve().parent.parent
    derived_dir = project_root / "data" / "derived" / "cell_lab_001"
    dataset_b_path = derived_dir / "dataset_b_falsification.json"

    if not dataset_b_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {dataset_b_path}")

    with open(dataset_b_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    observations = [Observation.model_validate(o) for o in payload["observations"]]
    evidences = [EvidenceRecord.model_validate(e) for e in payload["evidences"]]

    # Extrai o vetor de condicoes reais sob carga (ATP e forca de carga)
    test_conditions = []
    for obs in observations:
        mea = obs.measurements[0]
        test_conditions.append({
            "atp_concentration_uM": float(mea.conditions["atp_concentration_uM"]),
            "load_force_pN": float(mea.conditions["load_force_pN"]),
        })

    # Carrega o modelo calibrado no Dataset A
    model = build_kif5b_minimal_model(
        k_cat_default=103.92,
        k_m_default=94.63,
        step_size_default=8.2,
        calibration_evidence_id="DTS-CELL-LAB-001-CALIBRATION",
    )

    # Executa a simulacao com o modelo minimo (que ignora forca por premissa)
    simulation, predictions = run_kif5b_simulation(
        model=model,
        conditions=test_conditions,
        mode="analytical",
        dataset_version="1.0.0",
    )

    # Confronta as predicoes com as observacoes de forca
    report: ComparisonReport = compare_observations_and_predictions(
        observations=observations,
        predictions=predictions,
        model_id=model.id,
        simulation_id=simulation.id,
    )

    # Identifica evidencias sob carga (onde F_load > 0) que conflitam com o modelo
    conflicting_evidences = [
        e for e in evidences if float(e.conditions.get("load_force_pN", 0.0)) > 0.0
    ]

    # Cria o registro formal de conflito / contradicao (INV-CONFLICT-001)
    # Seleciona o ponto de maior discrepancia (stall force F = 6.0 pN em 1000 uM ATP)
    max_discrepancy_point = max(report.point_comparisons, key=lambda p: abs(p.z_score))
    evidence_stall = next(
        e for e in evidences if float(e.conditions.get("load_force_pN", 0.0)) == 6.0
    )

    conflict_record = ConflictRecord(
        id="CONF-KIF5B-LOAD-001",
        claim_a_id="CLM-REPRO-KIF5B-UNLOADED-001",
        claim_b_id=None,
        evidence_a_id="EVI-A-008",  # Ponto de 1000 uM ATP em carga nula de Dataset A
        evidence_b_id=evidence_stall.id,  # Ponto de 6.0 pN de Dataset B
        divergence_metric=(
            f"Colapso de predicao sob forca contraria de 6.0 pN: modelo preve "
            f"{max_discrepancy_point.predicted_value} um/s, mas valor empirico e "
            f"{max_discrepancy_point.observed_value} um/s (escore z = {max_discrepancy_point.z_score:.1f} sigma)."
        ),
        conditions_comparison={
            "conflicting_parameter": "load_force_pN",
            "model_assumption": "unloaded_motility_zero_force",
            "empirical_condition": "opposing_load_force_up_to_6pN",
            "atp_concentration_uM": 1000.0,
        },
        resolution_status=ConflictResolutionStatus.EXPLAINED_BY_CONDITIONS,
        resolution_notes=(
            "A discrepancia extrema decorre da premissa simplificadora 2 do modelo (F_load = 0.0 pN). "
            "Sob forca contraria, a barreira de energia de transicao conformacional aumenta "
            "exponencialmente (taxa de Bell/Kramers k(F) = k0 * exp(-F*delta_x / k_B*T)). "
            "O modelo de 2 estados Michaelis-Menten carece de acoplamento mecanoquimico dependente de carga."
        ),
    )

    # Registra o Claim epistemico de refutacao / contradicao
    falsification_claim = Claim(
        id="CLM-FALSIF-KIF5B-LOAD-001",
        statement=(
            "O modelo cinetico MOD-KIF5B-MINIMAL-MM e empiricamente refutado para regimes sob "
            "forca de carga contraria (F_load > 0 pN), divergindo em ate 49.8 desvios-padrao "
            "na forca de parada (stall force ~6 pN)."
        ),
        subject_entity_id="ENT-KIF5B-HUMAN",
        predicate="fails_under_opposing_load",
        object_entity_id=model.id,
        epistemic_record=EpistemicRecord(
            status=EpistemicStatus.CONTRADICTED,
            data_tier=DataTier.DERIVED,
            basis=[e.id for e in conflicting_evidences],
            conditions={
                "tested_loads_pN": [1.05, 2.15, 3.25, 4.30, 5.20, 6.00],
                "r_squared": report.metrics["r_squared"],
                "max_z_score": report.metrics["max_z_score"],
            },
            limitations=[
                "Refutacao valida especificamente para a aplicacao do modelo MOD-KIF5B-MINIMAL-MM sob carga contraria.",
                "Nao invalida o sucesso da reproducao sob regime estritamente desimpedido (carga zero)."
            ],
            confidence_evidence_count=len(conflicting_evidences),
        ),
        supporting_evidence_ids=[],
        conflicting_evidence_ids=[e.id for e in conflicting_evidences],
    )

    output_report = {
        "falsification_phenomenon": "CELL-LAB-001",
        "dataset_evaluated": "DTS-CELL-LAB-001-FALSIFICATION",
        "model_id": model.id,
        "simulation_id": simulation.id,
        "execution_hash": simulation.execution_hash,
        "comparison": report.model_dump(mode="json"),
        "conflict_record": conflict_record.model_dump(mode="json"),
        "falsification_claim": falsification_claim.model_dump(mode="json"),
    }

    report_path = derived_dir / "falsification_report_dataset_b.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(output_report, f, indent=2, ensure_ascii=False)

    print(f"Relatorio de Falsificacao salvo em: {report_path}")
    print(f"Veredito: {report.verdict}")
    print(f"R2: {report.metrics['r_squared']:.4f} | Escore z maximo: {report.metrics['max_z_score']:.1f}")
    print(f"Pontos dentro de 2 sigma: {report.metrics['within_2_sigma_count']}/{report.metrics['sample_count']}")

    return output_report


if __name__ == "__main__":
    execute_dataset_b_falsification()
