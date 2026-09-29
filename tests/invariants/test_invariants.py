"""Testes de inviolabilidade dos invariantes epistemica e regras de integridade cientifica."""

import pytest
from pydantic import ValidationError

from domain import (
    EvidenceRecord,
    Claim,
    Model,
    Parameter,
    ParameterEpistemicOrigin,
    Simulation,
    Prediction,
    Quantity,
    StandardUnit,
    UncertaintyType,
    EpistemicRecord,
    EpistemicStatus,
    DataTier,
    SoftLifecycleStatus,
)
from validation import (
    InvariantViolationError,
    verify_inv_evidence_001,
    verify_inv_data_001,
    verify_inv_claim_001,
    verify_inv_prediction_001,
    verify_inv_model_001,
    verify_inv_repro_001,
)


def test_inv_evidence_001_requires_source_and_experiment():
    # Sem source_id
    with pytest.raises(ValidationError, match="INV-EVIDENCE-001"):
        EvidenceRecord(
            source_id="",
            experiment_id="EXP-001",
            epistemic_record=EpistemicRecord(
                status=EpistemicStatus.OBSERVED,
                data_tier=DataTier.RAW,
            ),
        )

    # Sem experiment_id
    with pytest.raises(ValidationError, match="INV-EVIDENCE-001"):
        EvidenceRecord(
            source_id="SRC-001",
            experiment_id="   ",
            epistemic_record=EpistemicRecord(
                status=EpistemicStatus.OBSERVED,
                data_tier=DataTier.RAW,
            ),
        )


def test_inv_data_001_evidence_cannot_be_generated():
    # Evidencia nao pode pertencer a tier GENERATED
    with pytest.raises(ValidationError, match="INV-DATA-001"):
        EvidenceRecord(
            source_id="SRC-001",
            experiment_id="EXP-001",
            epistemic_record=EpistemicRecord(
                status=EpistemicStatus.INFERRED,
                data_tier=DataTier.GENERATED,
            ),
        )


def test_inv_claim_001_requires_supporting_evidence_for_grounded_status():
    # Claim OBSERVED sem supporting_evidence_ids deve falhar
    with pytest.raises(ValidationError, match="INV-CLAIM-001"):
        Claim(
            statement="KIF5B move-se a 0.8 um/s",
            subject_entity_id="ENT-KINESIN",
            predicate="moves_at",
            epistemic_record=EpistemicRecord(
                status=EpistemicStatus.OBSERVED,
                data_tier=DataTier.DERIVED,
            ),
            supporting_evidence_ids=[],
        )

    # Claim com status HYPOTHESIS pode ter lista vazia
    claim_hypo = Claim(
        statement="KIF5B possui um segundo sitio regulatorio de ATP",
        subject_entity_id="ENT-KINESIN",
        predicate="has_allosteric_site",
        epistemic_record=EpistemicRecord(
            status=EpistemicStatus.HYPOTHESIS,
            data_tier=DataTier.DERIVED,
        ),
        supporting_evidence_ids=[],
    )
    assert claim_hypo.epistemic_record.status == EpistemicStatus.HYPOTHESIS


def test_inv_prediction_001_requires_model_and_simulation():
    with pytest.raises(ValidationError, match="INV-PREDICTION-001"):
        Prediction(
            model_id="",
            simulation_id="SIM-001",
            predicted_property="velocity",
            quantity=Quantity(value=0.8, unit=StandardUnit.MICROMETER_PER_SECOND),
            epistemic_record=EpistemicRecord(
                status=EpistemicStatus.PREDICTED,
                data_tier=DataTier.GENERATED,
            ),
        )


def test_inv_model_001_requires_assumptions_and_parameters():
    param = Parameter(
        name="k_cat",
        description="taxa",
        unit=StandardUnit.PER_SECOND,
        origin=ParameterEpistemicOrigin.MEASURED,
    )

    # Sem premissas
    with pytest.raises(ValidationError):
        Model(
            name="Model_Sem_Premissas",
            description="desc",
            target_phenomenon="transporte",
            assumptions=[],
            parameters=[param],
            equations_or_algorithm_description="v = k",
            implementation_reference="models.test:run",
        )

    # Sem parametros
    with pytest.raises(ValidationError):
        Model(
            name="Model_Sem_Parametros",
            description="desc",
            target_phenomenon="transporte",
            assumptions=["Premissa 1"],
            parameters=[],
            equations_or_algorithm_description="v = k",
            implementation_reference="models.test:run",
        )


def test_quantity_uncertainty_consistency():
    # Incerteza numerica sem definir o tipo de incerteza deve falhar
    with pytest.raises(ValidationError, match="uncertainty_type diferente de 'none'"):
        Quantity(
            value=0.82,
            unit=StandardUnit.MICROMETER_PER_SECOND,
            uncertainty=0.04,
            uncertainty_type=UncertaintyType.NONE,
        )

    # Tipo de incerteza definido sem valor numerico deve falhar
    with pytest.raises(ValidationError, match="sem valor de incerteza numerico"):
        Quantity(
            value=0.82,
            unit=StandardUnit.MICROMETER_PER_SECOND,
            uncertainty=None,
            uncertainty_type=UncertaintyType.STANDARD_ERROR,
        )


def test_epistemic_integrity_cross_checks():
    # RAW com MODELED
    with pytest.raises(ValidationError, match="data_tier RAW nao pode possuir status MODELED"):
        EpistemicRecord(
            status=EpistemicStatus.MODELED,
            data_tier=DataTier.RAW,
        )

    # GENERATED com OBSERVED
    with pytest.raises(ValidationError, match="data_tier GENERATED nao pode ser rotulado como OBSERVED"):
        EpistemicRecord(
            status=EpistemicStatus.OBSERVED,
            data_tier=DataTier.GENERATED,
        )


def test_semver_validation():
    # Versao invalida
    with pytest.raises(ValidationError, match="Versao semantica invalida"):
        Parameter(
            name="k",
            description="taxa",
            unit=StandardUnit.PER_SECOND,
            origin=ParameterEpistemicOrigin.ESTIMATED,
        )
        # Testando em um modelo que herda de BaseDomainModel
        Claim(
            version="1.0-beta",
            statement="Afirmacao teste",
            subject_entity_id="ENT-1",
            predicate="binds",
            epistemic_record=EpistemicRecord(
                status=EpistemicStatus.HYPOTHESIS,
                data_tier=DataTier.DERIVED,
            ),
        )
