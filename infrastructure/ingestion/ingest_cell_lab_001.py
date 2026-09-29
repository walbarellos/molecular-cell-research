"""Pipeline de Ingestao, Normalizacao e Controle de Qualidade para CELL-LAB-001."""

import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, List, Tuple

# Garante inclusao do projeto no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from domain import (
    Dataset,
    Source,
    SourceType,
    Experiment,
    Observation,
    Measurement,
    EvidenceRecord,
    Entity,
    EntityCategory,
    EntityType,
    ExternalIdentifier,
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


def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_or_create_base_entities() -> Tuple[Entity, Entity]:
    kinesin = Entity(
        id="ENT-KIF5B-HUMAN",
        category=EntityCategory.BIOLOGICAL,
        entity_type=EntityType.PROTEIN,
        canonical_name="KIF5B",
        systematic_name="Kinesin-1 heavy chain (homodimer)",
        external_identifiers=[
            ExternalIdentifier(database_name="UniProt", accession_code="P33176"),
            ExternalIdentifier(database_name="PDB", accession_code="1BG2"),
        ],
        metadata={"organism": "Homo sapiens / Bos taurus / Loligo pealeii homolog"},
    )

    microtubule = Entity(
        id="ENT-MICROTUBULE-TAXOL",
        category=EntityCategory.PHYSICAL,
        entity_type=EntityType.FILAMENT,
        canonical_name="Microtubule",
        systematic_name="Taxol-stabilized porcine/bovine tubulin polymer",
        external_identifiers=[
            ExternalIdentifier(database_name="PDB", accession_code="1JFF")
        ],
        metadata={"lattice": "13-protofilament B-lattice"},
    )
    return kinesin, microtubule


def ingest_dataset_a(raw_csv_path: Path, kinesin: Entity) -> Tuple[Dataset, Source, Experiment, List[Observation], List[EvidenceRecord]]:
    sha256_hash = compute_sha256(raw_csv_path)

    source = Source(
        id="SRC-SCHNITZER-1997",
        source_type=SourceType.JOURNAL_ARTICLE,
        identifier="10.1038/41111",
        title="Kinesin hydrolyses one ATP per 8-nm step",
        authors=["Schnitzer, M. J.", "Block, S. M."],
        year=1997,
        publication_venue="Nature",
        uri="https://doi.org/10.1038/41111",
        content_hash_sha256=sha256_hash,
    )

    experiment = Experiment(
        id="EXP-SCHNITZER-1997-MOTILITY",
        source_id=source.id,
        name="Unloaded single-molecule kinesin motility across ATP gradient",
        method="optical_trap_tracking",
        protocol_description="Measurement of bead translocation velocity over taxol-stabilized microtubules in BRB80 buffer at 24 degC with load force = 0 pN.",
        environmental_conditions={
            "temperature_degC": 24.0,
            "buffer": "BRB80",
            "load_force_pN": 0.0,
        },
    )

    observations: List[Observation] = []
    evidences: List[EvidenceRecord] = []

    with open(raw_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader((row for row in f if not row.startswith("#")))
        for idx, row in enumerate(reader):
            atp_uM = float(row["atp_concentration_uM"])
            v_um_s = float(row["velocity_um_s"])
            unc_um_s = float(row["uncertainty_um_s"])
            unc_type_str = row["uncertainty_type"]
            n_samples = int(row["sample_size_n"])
            temp_degC = float(row["temperature_degC"])

            # Controle de Qualidade (Quality Control)
            if atp_uM <= 0 or v_um_s < 0 or unc_um_s < 0:
                raise ValueError(f"Violacao de QC no registro {idx} de {raw_csv_path.name}")

            unc_type = UncertaintyType(unc_type_str)

            measurement = Measurement(
                id=f"MEA-A-{idx:03d}",
                quantity=Quantity(
                    value=v_um_s,
                    unit=StandardUnit.MICROMETER_PER_SECOND,
                    uncertainty=unc_um_s,
                    uncertainty_type=unc_type,
                    representation=RepresentationType.POINT_ESTIMATE,
                ),
                measured_property="velocity",
                entity_id=kinesin.id,
                conditions={
                    "atp_concentration_uM": atp_uM,
                    "load_force_pN": 0.0,
                    "temperature_degC": temp_degC,
                    "sample_size_n": n_samples,
                },
                method="optical_trap_tracking",
            )

            obs = Observation(
                id=f"OBS-A-{idx:03d}",
                experiment_id=experiment.id,
                description=f"KIF5B unloaded velocity at {atp_uM} uM ATP: {v_um_s} um/s",
                measurements=[measurement],
                raw_data_ref=f"{raw_csv_path.name}:row_{idx+1}",
            )
            measurement.observation_id = obs.id
            observations.append(obs)

            evidence = EvidenceRecord(
                id=f"EVI-A-{idx:03d}",
                source_id=source.id,
                experiment_id=experiment.id,
                observation_ids=[obs.id],
                conditions={
                    "atp_concentration_uM": atp_uM,
                    "load_force_pN": 0.0,
                    "temperature_degC": temp_degC,
                },
                epistemic_record=EpistemicRecord(
                    status=EpistemicStatus.OBSERVED,
                    data_tier=DataTier.RAW,
                    provenance=ProvenanceRecord(
                        source_uri=f"doi:{source.identifier}",
                        method="optical_trap_tracking",
                        operator=OperatorType.HUMAN,
                        conditions={"atp_uM": atp_uM, "load_pN": 0.0},
                    ),
                    limitations=["In vitro unloaded motility in BRB80 buffer; single-molecule."],
                    confidence_evidence_count=1,
                ),
            )
            evidences.append(evidence)

    dataset = Dataset(
        id="DTS-CELL-LAB-001-CALIBRATION",
        name="CELL-LAB-001-Dataset-A-Calibration",
        data_tier=DataTier.RAW,
        description="Dataset A: Calibracao cinetica de velocidade em funcao de [ATP] em carga nula (Schnitzer & Block 1997).",
        source_ids=[source.id],
        storage_uri=str(raw_csv_path),
        checksum_sha256=sha256_hash,
        parameters_schema={
            "independent_variables": ["atp_concentration_uM"],
            "dependent_variables": ["velocity_um_s"],
            "constants": {"load_force_pN": 0.0, "temperature_degC": 24.0},
        },
        record_count=len(observations),
    )

    return dataset, source, experiment, observations, evidences


def ingest_dataset_b(raw_csv_path: Path, kinesin: Entity) -> Tuple[Dataset, Source, Experiment, List[Observation], List[EvidenceRecord]]:
    sha256_hash = compute_sha256(raw_csv_path)

    source = Source(
        id="SRC-VISSCHER-1999",
        source_type=SourceType.JOURNAL_ARTICLE,
        identifier="10.1038/22146",
        title="Single kinesin molecules studied with a molecular force clamp",
        authors=["Visscher, K.", "Schnitzer, M. J.", "Block, S. M."],
        year=1999,
        publication_venue="Nature",
        uri="https://doi.org/10.1038/22146",
        content_hash_sha256=sha256_hash,
    )

    experiment = Experiment(
        id="EXP-VISSCHER-1999-FORCE-CLAMP",
        source_id=source.id,
        name="Force-dependent single-molecule kinesin motility under optical force clamp",
        method="optical_force_clamp",
        protocol_description="Single kinesin bead translocation under feedback-controlled constant opposing loads (0 to 6 pN) at saturating and limiting ATP.",
        environmental_conditions={
            "temperature_degC": 24.0,
            "buffer": "BRB80",
        },
    )

    observations: List[Observation] = []
    evidences: List[EvidenceRecord] = []

    with open(raw_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader((row for row in f if not row.startswith("#")))
        for idx, row in enumerate(reader):
            load_pN = float(row["load_force_pN"])
            atp_uM = float(row["atp_concentration_uM"])
            v_um_s = float(row["velocity_um_s"])
            unc_um_s = float(row["uncertainty_um_s"])
            unc_type_str = row["uncertainty_type"]
            n_samples = int(row["sample_size_n"])
            temp_degC = float(row["temperature_degC"])

            # Controle de Qualidade (Quality Control)
            if atp_uM <= 0 or v_um_s < 0 or unc_um_s < 0 or load_pN < 0:
                raise ValueError(f"Violacao de QC no registro {idx} de {raw_csv_path.name}")

            unc_type = UncertaintyType(unc_type_str)

            measurement = Measurement(
                id=f"MEA-B-{idx:03d}",
                quantity=Quantity(
                    value=v_um_s,
                    unit=StandardUnit.MICROMETER_PER_SECOND,
                    uncertainty=unc_um_s,
                    uncertainty_type=unc_type,
                    representation=RepresentationType.POINT_ESTIMATE,
                ),
                measured_property="velocity",
                entity_id=kinesin.id,
                conditions={
                    "load_force_pN": load_pN,
                    "atp_concentration_uM": atp_uM,
                    "temperature_degC": temp_degC,
                    "sample_size_n": n_samples,
                },
                method="optical_force_clamp",
            )

            obs = Observation(
                id=f"OBS-B-{idx:03d}",
                experiment_id=experiment.id,
                description=f"KIF5B velocity under {load_pN} pN opposing load at {atp_uM} uM ATP: {v_um_s} um/s",
                measurements=[measurement],
                raw_data_ref=f"{raw_csv_path.name}:row_{idx+1}",
            )
            measurement.observation_id = obs.id
            observations.append(obs)

            evidence = EvidenceRecord(
                id=f"EVI-B-{idx:03d}",
                source_id=source.id,
                experiment_id=experiment.id,
                observation_ids=[obs.id],
                conditions={
                    "load_force_pN": load_pN,
                    "atp_concentration_uM": atp_uM,
                    "temperature_degC": temp_degC,
                },
                epistemic_record=EpistemicRecord(
                    status=EpistemicStatus.OBSERVED,
                    data_tier=DataTier.RAW,
                    provenance=ProvenanceRecord(
                        source_uri=f"doi:{source.identifier}",
                        method="optical_force_clamp",
                        operator=OperatorType.HUMAN,
                        conditions={"load_pN": load_pN, "atp_uM": atp_uM},
                    ),
                    limitations=["In vitro optical force-clamp; forces applied parallel to microtubule axis."],
                    confidence_evidence_count=1,
                ),
            )
            evidences.append(evidence)

    dataset = Dataset(
        id="DTS-CELL-LAB-001-FALSIFICATION",
        name="CELL-LAB-001-Dataset-B-Falsification",
        data_tier=DataTier.RAW,
        description="Dataset B: Teste/Falsificacao de relacoes forca-velocidade sob forca contraria (Visscher et al. 1999).",
        source_ids=[source.id],
        storage_uri=str(raw_csv_path),
        checksum_sha256=sha256_hash,
        parameters_schema={
            "independent_variables": ["load_force_pN", "atp_concentration_uM"],
            "dependent_variables": ["velocity_um_s"],
            "constants": {"temperature_degC": 24.0},
        },
        record_count=len(observations),
    )

    return dataset, source, experiment, observations, evidences


def run_pipeline() -> None:
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw" / "cell_lab_001"
    derived_dir = project_root / "data" / "derived" / "cell_lab_001"
    derived_dir.mkdir(parents=True, exist_ok=True)

    kinesin, microtubule = get_or_create_base_entities()

    # Processa Dataset A
    path_a = raw_dir / "schnitzer_block_1997_unloaded_velocity.csv"
    dts_a, src_a, exp_a, obs_a, evi_a = ingest_dataset_a(path_a, kinesin)

    payload_a = {
        "dataset": dts_a.model_dump(mode="json"),
        "source": src_a.model_dump(mode="json"),
        "experiment": exp_a.model_dump(mode="json"),
        "observations": [o.model_dump(mode="json") for o in obs_a],
        "evidences": [e.model_dump(mode="json") for e in evi_a],
    }

    out_a = derived_dir / "dataset_a_calibration.json"
    with open(out_a, "w", encoding="utf-8") as f:
        json.dump(payload_a, f, indent=2, ensure_ascii=False)
    print(f"Dataset A normalizado salvo em: {out_a}")

    # Processa Dataset B
    path_b = raw_dir / "visscher_block_1999_force_velocity.csv"
    dts_b, src_b, exp_b, obs_b, evi_b = ingest_dataset_b(path_b, kinesin)

    payload_b = {
        "dataset": dts_b.model_dump(mode="json"),
        "source": src_b.model_dump(mode="json"),
        "experiment": exp_b.model_dump(mode="json"),
        "observations": [o.model_dump(mode="json") for o in obs_b],
        "evidences": [e.model_dump(mode="json") for e in evi_b],
    }

    out_b = derived_dir / "dataset_b_falsification.json"
    with open(out_b, "w", encoding="utf-8") as f:
        json.dump(payload_b, f, indent=2, ensure_ascii=False)
    print(f"Dataset B normalizado salvo em: {out_b}")

    # Manifesto de Curadoria de CELL-LAB-001
    manifest = {
        "phenomenon": "CELL-LAB-001",
        "description": "Curated empirical datasets for kinesin-1 motility calibration and falsification",
        "entities": {
            "kinesin": kinesin.model_dump(mode="json"),
            "microtubule": microtubule.model_dump(mode="json"),
        },
        "datasets": {
            "calibration_dataset_a": {
                "id": dts_a.id,
                "name": dts_a.name,
                "sha256": dts_a.checksum_sha256,
                "source_doi": src_a.identifier,
                "record_count": dts_a.record_count,
                "role": "Model calibration (unloaded velocity vs [ATP])",
            },
            "falsification_dataset_b": {
                "id": dts_b.id,
                "name": dts_b.name,
                "sha256": dts_b.checksum_sha256,
                "source_doi": src_b.identifier,
                "record_count": dts_b.record_count,
                "role": "Model falsification (load force vs velocity)",
            },
        },
    }

    out_manifest = derived_dir / "manifest_cell_lab_001.json"
    with open(out_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"Manifesto CELL-LAB-001 salvo em: {out_manifest}")


if __name__ == "__main__":
    run_pipeline()
