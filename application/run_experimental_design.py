"""Pipeline de Orquestracao de Desenho Experimental Discriminatorio (Ciclo 09)."""

import json
from pathlib import Path
import sys
from typing import Dict, Any

# Garante path do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain import (
    Hypothesis,
    ExperimentDesign,
    EpistemicRecord,
    EpistemicStatus,
    DataTier,
)
from analysis.discriminator import design_optimal_discriminatory_experiment


def execute_experimental_design_cycle() -> Dict[str, Any]:
    project_root = Path(__file__).resolve().parent.parent
    derived_dir = project_root / "data" / "derived" / "cell_lab_001"
    derived_dir.mkdir(parents=True, exist_ok=True)

    # Executa a busca pelo experimento otimo
    exp_design, evaluations = design_optimal_discriminatory_experiment()

    # Formula a Hipotese Cientifica de L4/L5 candidata (Ciclo 09)
    hypothesis = Hypothesis(
        id="HYP-KIF5B-KRAMERS-COUPLING-001",
        statement=(
            "O avanço de KIF5B sob forca contraria e governado por transicoes conformacionais do neck linker "
            "com taxa catalitica dependente de energia de deformacao mecânica (k_cat(F) = k_cat_0 * exp(-F*delta / k_B*T)), "
            "prevendo cessacao de avanço proximo a stall force de ~6.0 pN."
        ),
        rationale=(
            "A refutacao sistematica de ate 50 sigma observada no modelo M1 sob carga contraria (CONF-KIF5B-LOAD-001) "
            "exige a introducao de um termo mecanoquimico exponencial dependente de carga."
        ),
        competing_model_ids=exp_design.competing_model_ids,
        falsification_criteria=[
            "Se em ensaio com carga contraria de 5.0 pN e 1000 uM ATP a velocidade for > 0.5 um/s, M2 e falsificado.",
            "Se em ensaio com carga contraria de 5.0 pN e 1000 uM ATP a velocidade for < 0.4 um/s, M1 e falsificado.",
        ],
        epistemic_record=EpistemicRecord(
            status=EpistemicStatus.HYPOTHESIS,
            data_tier=DataTier.DERIVED,
            basis=["CONF-KIF5B-LOAD-001", "DTS-CELL-LAB-001-FALSIFICATION"],
            conditions={"temperature_degC": 24.0, "buffer": "BRB80"},
            limitations=["Hipotese computacional candidata sujeita a ensaios discriminatorios adicionais."],
            confidence_evidence_count=0,
        ),
    )

    # Top 5 condicoes ranqueadas
    top_candidates = [e.model_dump(mode="json") for e in evaluations[:5]]

    output_payload = {
        "cycle": "CICLO_09_EXPERIMENTAL_DESIGN",
        "phenomenon": "CELL-LAB-001",
        "target_hypothesis": hypothesis.model_dump(mode="json"),
        "optimal_experiment_design": exp_design.model_dump(mode="json"),
        "top_5_discriminatory_conditions": top_candidates,
        "total_conditions_evaluated": len(evaluations),
    }

    out_file = derived_dir / "experiment_design_cell_lab_001.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2, ensure_ascii=False)

    print(f"Desenho Experimental salvo em: {out_file}")
    print(f"Experimento Recomendado: {exp_design.title}")
    print(f"Condicao Otima: [ATP] = {exp_design.target_conditions['atp_concentration_uM']} uM | Carga = {exp_design.target_conditions['load_force_pN']} pN")
    print(f"Poder Discriminatorio: {exp_design.discriminatory_power_score*100:.1f}%")
    print(f"  M1 preve: {exp_design.predicted_outcomes[exp_design.competing_model_ids[0]]}")
    print(f"  M2 preve: {exp_design.predicted_outcomes[exp_design.competing_model_ids[1]]}")

    return output_payload


if __name__ == "__main__":
    execute_experimental_design_cycle()
