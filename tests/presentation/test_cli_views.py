"""Testes automatizados da Camada L7: ViewModels, Modos de Visualizacao e CLI."""

import pytest

from application.exploration_service import (
    get_system_overview,
    simulate_user_mode,
    get_engineer_view,
    get_scientist_view,
)
from presentation.cli.user_view import render_user_view
from presentation.cli.engineer_view import render_engineer_view
from presentation.cli.scientist_view import render_scientist_view
from presentation.cli.main import build_parser


def test_system_overview():
    dto = get_system_overview()
    assert dto.phenomenon == "CELL-LAB-001 (KIF5B Motility on Microtubule)"
    assert dto.total_sources == 2
    assert dto.total_experiments == 2
    assert dto.total_observations == 21
    assert dto.total_evidences == 21
    assert dto.validated_claims == 1
    assert dto.contradicted_claims == 1
    assert dto.total_conflicts == 1


def test_user_mode_epistemic_firewall():
    # Condicao validada (carga zero)
    dto_unloaded = simulate_user_mode(atp_uM=1000.0, load_pN=0.0)
    assert dto_unloaded.data_tier == "GENERATED"
    assert dto_unloaded.epistemic_status == "PREDICTED"
    assert dto_unloaded.is_within_validated_envelope is True
    assert dto_unloaded.epistemic_warning is None
    assert 0.75 <= dto_unloaded.predicted_velocity_um_s <= 0.82

    # Condicao refutada (sob forca)
    dto_loaded = simulate_user_mode(atp_uM=1000.0, load_pN=4.0)
    assert dto_loaded.data_tier == "GENERATED"
    assert dto_loaded.epistemic_status == "PREDICTED"
    assert dto_loaded.is_within_validated_envelope is False
    assert dto_loaded.epistemic_warning is not None
    assert "REFUTADO" in dto_loaded.epistemic_warning

    # Renderizacao
    text = render_user_view(dto_loaded)
    assert "MODO USUARIO" in text
    assert "ALERTA DE FRONTEIRA" in text


def test_engineer_mode_inspection():
    dto = get_engineer_view()
    assert len(dto.entities) == 2
    assert dto.model_name == "KIF5B_Minimal_2State_MichaelisMenten"
    assert len(dto.parameters) == 3
    assert dto.supporting_evidence_count == 10

    # Renderizacao
    text = render_engineer_view(dto)
    assert "MODO ENGENHEIRO" in text
    assert "KIF5B" in text
    assert "k_cat" in text
    assert "Stall Force" in text


def test_scientist_mode_provenance_and_conflicts():
    dto = get_scientist_view()
    assert dto.active_model_id == "MOD-KIF5B-MINIMAL-MM"
    assert len(dto.assumptions) >= 4
    assert len(dto.active_claims) == 2
    assert len(dto.conflicts) == 1

    # Confere presenca dos claims validados e refutados
    statuses = [c["epistemic_record"]["status"] for c in dto.active_claims]
    assert "VALIDATED" in statuses
    assert "CONTRADICTED" in statuses

    # Confere presenca do conflito formal
    conf = dto.conflicts[0]
    assert conf["id"] == "CONF-KIF5B-LOAD-001"
    assert conf["resolution_status"] == "explained_by_conditions"

    # Renderizacao
    text = render_scientist_view(dto)
    assert "MODO CIENTIFICO" in text
    assert "Trilha de Proveniencia" in text
    assert "CLM-REPRO-KIF5B-UNLOADED-001" in text
    assert "CLM-FALSIF-KIF5B-LOAD-001" in text
    assert "CONF-KIF5B-LOAD-001" in text


def test_cli_parser_arguments():
    parser = build_parser()

    args_status = parser.parse_args(["status"])
    assert args_status.command == "status"

    args_user = parser.parse_args(["user", "--atp", "500", "--load", "2.5"])
    assert args_user.command == "user"
    assert args_user.atp == 500.0
    assert args_user.load == 2.5

    args_eng = parser.parse_args(["engineer"])
    assert args_eng.command == "engineer"

    args_sci = parser.parse_args(["scientist"])
    assert args_sci.command == "scientist"
