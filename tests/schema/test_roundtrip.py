"""Teste de Roundtrip e Serializacao: Definition of Done do Ciclo 02.

Valida a cadeia epistemica completa:
SOURCE -> EXPERIMENT -> OBSERVATION -> EVIDENCE -> CLAIM -> MODEL -> SIMULATION -> PREDICTION

Garante que:
mesma entrada + mesma versao + mesmos parametros = mesmo estado reconstruivel
sem perda de unidades, incertezas, proveniencia, condicoes, status epistemico ou relacoes.
"""

import json
from pathlib import Path
import pytest

from domain import (
    Source,
    SourceType,
    Experiment,
    Observation,
    EvidenceRecord,
    Entity,
    EntityCategory,
    EntityType,
    ExternalIdentifier,
    Relation,
    RelationType,
    Claim,
    Model,
    Parameter,
    ParameterEpistemicOrigin,
    ModelValidationStatus,
    Simulation,
    Prediction,
    ConflictRecord,
    ConflictResolutionStatus,
    Quantity,
    Measurement,
    StandardUnit,
    UncertaintyType,
    RepresentationType,
    EpistemicRecord,
    EpistemicStatus,
    DataTier,
    ProvenanceRecord,
    OperatorType,
)
from validation import verify_chain_referential_integrity


def build_canonical_chain():
    # 1. Source
    source = Source(
        source_type=SourceType.JOURNAL_ARTICLE,
        identifier="10.1038/352261a0",
        title="Direct observation of single kinesin molecules moving along microtubules",
        authors=["Svoboda, K.", "Schmidt, C. F.", "Schnapp, B. J.", "Block, S. M."],
        year=1993,
        publication_venue="Nature",
        uri="https://doi.org/10.1038/352261a0",
        content_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )

    # 2. Experiment
    experiment = Experiment(
        source_id=source.id,
        name="Optical tweezers single-molecule kinesin motility assay",
        method="optical_trap_nanometry",
        protocol_description="In vitro motility of native KIF5B homodimer on taxol-stabilized microtubules",
        environmental_conditions={
            "temperature_degC": 25.0,
            "atp_concentration_mM": 1.0,
            "buffer": "BRB80",
            "ph": 6.9,
            "load_force_pN": 0.0,
        },
    )

    # Entidades de suporte
    kinesin = Entity(
        category=EntityCategory.BIOLOGICAL,
        entity_type=EntityType.PROTEIN,
        canonical_name="KIF5B",
        systematic_name="Kinesin-1 heavy chain",
        external_identifiers=[
            ExternalIdentifier(database_name="UniProt", accession_code="P33176")
        ],
        metadata={"organism": "Homo sapiens", "molecular_weight_kDa": 110.0},
    )

    microtubule = Entity(
        category=EntityCategory.PHYSICAL,
        entity_type=EntityType.FILAMENT,
        canonical_name="Microtubule",
        systematic_name="Taxol-stabilized tubulin polymer",
        metadata={"subunits": "alpha-beta tubulin heterodimer"},
    )

    # 3. Observation & Measurement
    velocity_measurement = Measurement(
        quantity=Quantity(
            value=0.82,
            unit=StandardUnit.MICROMETER_PER_SECOND,
            uncertainty=0.04,
            uncertainty_type=UncertaintyType.STANDARD_ERROR,
            representation=RepresentationType.POINT_ESTIMATE,
        ),
        measured_property="velocity",
        entity_id=kinesin.id,
        conditions={"atp_mM": 1.0, "load_pN": 0.0, "temp_degC": 25.0},
        method="optical_trap_tracking",
    )

    observation = Observation(
        experiment_id=experiment.id,
        description="Processive stepping velocity of KIF5B along microtubule under saturating ATP",
        measurements=[velocity_measurement],
        raw_data_ref="L2/raw/svoboda1993/velocity_traces_run01.csv",
    )
    velocity_measurement.observation_id = observation.id

    # 4. Evidence
    evidence = EvidenceRecord(
        source_id=source.id,
        experiment_id=experiment.id,
        observation_ids=[observation.id],
        conditions={"atp_mM": 1.0, "temperature_degC": 25.0},
        epistemic_record=EpistemicRecord(
            status=EpistemicStatus.OBSERVED,
            data_tier=DataTier.RAW,
            provenance=ProvenanceRecord(
                source_uri="doi:10.1038/352261a0",
                method="optical_trap_nanometry",
                operator=OperatorType.HUMAN,
                conditions={"atp_mM": 1.0},
            ),
            limitations=["In vitro assay; absent cytosolic crowding components."],
            confidence_evidence_count=1,
        ),
    )

    # 5. Claim
    claim = Claim(
        statement="KIF5B translocates processively toward the microtubule plus-end with velocity ~0.82 um/s at 1.0 mM ATP (25 degC)",
        subject_entity_id=kinesin.id,
        predicate="translocates_along",
        object_entity_id=microtubule.id,
        epistemic_record=EpistemicRecord(
            status=EpistemicStatus.OBSERVED,
            data_tier=DataTier.DERIVED,
            basis=[evidence.id],
            confidence_evidence_count=1,
        ),
        supporting_evidence_ids=[evidence.id],
    )
    evidence.supports_claims = [claim.id]

    # Relation
    relation = Relation(
        source_entity_id=kinesin.id,
        target_entity_id=microtubule.id,
        relation_type=RelationType.TRANSLOCATES_ALONG,
        supporting_evidence_ids=[evidence.id],
    )

    # 6. Model
    param_kcat = Parameter(
        name="k_cat",
        description="Maximum catalytic turnover rate per head",
        unit=StandardUnit.PER_SECOND,
        default_value=105.0,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id=evidence.id,
        sensitivity_bounds=[95.0, 115.0],
    )
    param_km = Parameter(
        name="K_m",
        description="Michaelis constant for ATP binding",
        unit=StandardUnit.MICROMOLAR,
        default_value=90.0,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id=evidence.id,
        sensitivity_bounds=[70.0, 110.0],
    )
    param_step = Parameter(
        name="step_size",
        description="Mechanical step distance per ATP hydrolyzed",
        unit=StandardUnit.NANOMETER,
        default_value=8.2,
        origin=ParameterEpistemicOrigin.MEASURED,
        evidence_id=evidence.id,
        sensitivity_bounds=[8.0, 8.4],
    )

    model = Model(
        name="KIF5B_Minimal_2State_MichaelisMenten",
        description="Minimal mechanochemical model linking ATP binding turnover to discrete 8.2 nm steps",
        target_phenomenon="KIF5B_unloaded_velocity",
        assumptions=[
            "Tight coupling: 1 ATP consumed per 8.2 nm physical step",
            "Hydrolysis and phosphate release are irreversible at initial velocity conditions",
            "Zero opposing load force (unloaded motility)",
        ],
        parameters=[param_kcat, param_km, param_step],
        inputs=["atp_concentration_uM"],
        outputs=["velocity_um_s"],
        equations_or_algorithm_description="v([ATP]) = (k_cat * [ATP] / (K_m + [ATP])) * d_step",
        implementation_reference="computation.models.kinesin_minimal:evaluate_velocity",
        source_reference="Schnitzer and Block 1997 / Svoboda et al. 1993",
        validation_status=ModelValidationStatus.PROVISIONALLY_CONSISTENT,
    )

    # 7. Simulation
    simulation = Simulation(
        model_id=model.id,
        model_version=model.version,
        dataset_version="1.0.0",
        parameter_overrides={"atp_concentration_uM": 1000.0},
        environment_info={"python": "3.14.7", "platform": "linux", "numpy": "none_pure_math"},
        random_seed=42,
        execution_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
        outputs={"computed_velocity_um_s": 0.818},
    )

    # 8. Prediction
    prediction = Prediction(
        model_id=model.id,
        simulation_id=simulation.id,
        predicted_property="velocity",
        quantity=Quantity(
            value=0.818,
            unit=StandardUnit.MICROMETER_PER_SECOND,
            uncertainty=0.035,
            uncertainty_type=UncertaintyType.STANDARD_DEVIATION,
            representation=RepresentationType.POINT_ESTIMATE,
        ),
        conditions={"atp_concentration_uM": 1000.0, "load_force_pN": 0.0},
        epistemic_record=EpistemicRecord(
            status=EpistemicStatus.PREDICTED,
            data_tier=DataTier.GENERATED,
            provenance=ProvenanceRecord(
                source_uri=f"model:{model.id}",
                method="analytical_evaluation",
                operator=OperatorType.MODEL,
                conditions={"atp_uM": 1000.0},
            ),
            confidence_evidence_count=1,
        ),
    )
    simulation.predictions = [prediction]

    # Conflito representativo (condicoes de temperatura distintas)
    conflict = ConflictRecord(
        evidence_a_id=evidence.id,
        evidence_b_id="EVID-SAMPLE-COLD-TEMP",
        divergence_metric="Velocidade em 20 degC (0.45 um/s) vs 25 degC (0.82 um/s)",
        conditions_comparison={
            "temperature_a_degC": 25.0,
            "temperature_b_degC": 20.0,
            "arrhenius_expected": True,
        },
        resolution_status=ConflictResolutionStatus.EXPLAINED_BY_CONDITIONS,
        resolution_notes="A divergencia decorre da sensibilidade termica da taxa catalitica k_cat (Q10 ~ 2.0).",
    )

    return {
        "source": source,
        "experiment": experiment,
        "kinesin": kinesin,
        "microtubule": microtubule,
        "observation": observation,
        "evidence": evidence,
        "claim": claim,
        "relation": relation,
        "model": model,
        "simulation": simulation,
        "prediction": prediction,
        "conflict": conflict,
    }


def test_chain_referential_integrity():
    chain = build_canonical_chain()
    # Verifica que a cadeia passa na integridade referencial formal
    verify_chain_referential_integrity(
        source=chain["source"],
        experiment=chain["experiment"],
        observation=chain["observation"],
        evidence=chain["evidence"],
        claim=chain["claim"],
        model=chain["model"],
        simulation=chain["simulation"],
        prediction=chain["prediction"],
    )


def test_full_chain_serialization_roundtrip(tmp_path: Path):
    chain = build_canonical_chain()

    # Serializa todos os objetos em um dicionario JSON canonical
    serialized_payload = {
        key: obj.model_dump(mode="json")
        for key, obj in chain.items()
    }

    json_str = json.dumps(serialized_payload, indent=2, ensure_ascii=False)
    assert len(json_str) > 0

    # Grava exemplo canônico em schemas/examples/
    example_path = Path(__file__).resolve().parent.parent.parent / "schemas" / "examples" / "canonical_chain_cell_lab_001.json"
    example_path.parent.mkdir(parents=True, exist_ok=True)
    with open(example_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Reconstrói a partir do JSON (Desserializacao estrita)
    deserialized_data = json.loads(json_str)

    reconstructed_chain = {
        "source": Source.model_validate(deserialized_data["source"]),
        "experiment": Experiment.model_validate(deserialized_data["experiment"]),
        "kinesin": Entity.model_validate(deserialized_data["kinesin"]),
        "microtubule": Entity.model_validate(deserialized_data["microtubule"]),
        "observation": Observation.model_validate(deserialized_data["observation"]),
        "evidence": EvidenceRecord.model_validate(deserialized_data["evidence"]),
        "claim": Claim.model_validate(deserialized_data["claim"]),
        "relation": Relation.model_validate(deserialized_data["relation"]),
        "model": Model.model_validate(deserialized_data["model"]),
        "simulation": Simulation.model_validate(deserialized_data["simulation"]),
        "prediction": Prediction.model_validate(deserialized_data["prediction"]),
        "conflict": ConflictRecord.model_validate(deserialized_data["conflict"]),
    }

    # Re-verifica a integridade referencial nos objetos reconstruidos
    verify_chain_referential_integrity(
        source=reconstructed_chain["source"],
        experiment=reconstructed_chain["experiment"],
        observation=reconstructed_chain["observation"],
        evidence=reconstructed_chain["evidence"],
        claim=reconstructed_chain["claim"],
        model=reconstructed_chain["model"],
        simulation=reconstructed_chain["simulation"],
        prediction=reconstructed_chain["prediction"],
    )

    # Validacao de equivalencia estrita de estado (Definition of Done)
    for key in chain:
        original_dict = chain[key].model_dump(mode="json")
        reconstructed_dict = reconstructed_chain[key].model_dump(mode="json")
        assert original_dict == reconstructed_dict, f"Divergencia detectada no roundtrip para o objeto: {key}"

    # Verificacao estrita de preservacao sem perda
    obs = reconstructed_chain["observation"]
    assert obs.measurements[0].quantity.unit == StandardUnit.MICROMETER_PER_SECOND
    assert obs.measurements[0].quantity.value == 0.82
    assert obs.measurements[0].quantity.uncertainty == 0.04
    assert obs.measurements[0].quantity.uncertainty_type == UncertaintyType.STANDARD_ERROR

    pred = reconstructed_chain["prediction"]
    assert pred.epistemic_record.data_tier == DataTier.GENERATED
    assert pred.epistemic_record.status == EpistemicStatus.PREDICTED
    assert pred.quantity.unit == StandardUnit.MICROMETER_PER_SECOND
    assert pred.quantity.value == 0.818
