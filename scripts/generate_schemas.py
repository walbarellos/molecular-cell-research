"""Script para geracao automatica de JSON Schemas a partir dos modelos Pydantic v2."""

import json
from pathlib import Path
import sys

# Garante inclusao do projeto no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from domain import (
    Dataset,
    Source,
    Experiment,
    Observation,
    EvidenceRecord,
    Entity,
    Relation,
    Claim,
    Model,
    Parameter,
    Simulation,
    Prediction,
    Hypothesis,
    ExperimentDesign,
    ConflictRecord,
    Quantity,
    Measurement,
    EpistemicRecord,
)

MODELS_TO_EXPORT = {
    "dataset": Dataset,
    "source": Source,
    "experiment": Experiment,
    "observation": Observation,
    "evidence_record": EvidenceRecord,
    "entity": Entity,
    "relation": Relation,
    "claim": Claim,
    "model": Model,
    "parameter": Parameter,
    "simulation": Simulation,
    "prediction": Prediction,
    "hypothesis": Hypothesis,
    "experiment_design": ExperimentDesign,
    "conflict_record": ConflictRecord,
    "quantity": Quantity,
    "measurement": Measurement,
    "epistemic_record": EpistemicRecord,
}


def export_schemas() -> None:
    output_dir = Path(__file__).resolve().parent.parent / "schemas" / "json"
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, model_cls in MODELS_TO_EXPORT.items():
        schema_path = output_dir / f"{name}.schema.json"
        schema_dict = model_cls.model_json_schema()
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema_dict, f, indent=2, ensure_ascii=False)
        print(f"Exportado: {schema_path.name}")


if __name__ == "__main__":
    export_schemas()
