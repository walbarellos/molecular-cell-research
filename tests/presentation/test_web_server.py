"""Testes de integracao para o Servidor Web FastAPI e Dashboard L7 (Ciclo 11)."""

import pytest
from starlette.testclient import TestClient
from presentation.web.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_web_root_spa(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "CELL LAB" in response.text
    assert "Scientific Systems Exploration Platform" in response.text
    assert "Epistemic Firewall" in response.text


def test_api_status(client):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_models"] == 4
    assert data["total_sources"] == 2
    assert data["total_claims"] == 2


def test_api_simulate_kinesin_valid(client):
    payload = {"atp_uM": 1000.0, "load_pN": 0.0, "model_id": "MOD-KIF5B-MINIMAL-MM"}
    response = client.post("/api/simulate/kinesin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["user_state"]["is_within_validated_envelope"] is True
    assert "force_velocity_curve" in data["curves"]
    assert "dataset_a" in data["empirical_data"]


def test_api_simulate_kinesin_refuted_firewall(client):
    payload = {"atp_uM": 1000.0, "load_pN": 4.0, "model_id": "MOD-KIF5B-MINIMAL-MM"}
    response = client.post("/api/simulate/kinesin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_state"]["is_within_validated_envelope"] is False
    assert "REFUTADO" in data["user_state"]["epistemic_warning"]


def test_api_simulate_tug_of_war(client):
    payload = {"num_kinesins": 3, "num_dyneins": 3, "external_load_pN": 0.0, "duration_s": 2.0}
    response = client.post("/api/simulate/tug-of-war", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "trajectory" in data
    assert "steady_state_distribution" in data


def test_api_simulate_langevin(client):
    payload = {"atp_uM": 1000.0, "trap_stiffness_pN_nm": 0.04, "total_time_ms": 20.0, "dt_us": 2.0}
    response = client.post("/api/simulate/langevin", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "points" in data
    assert data["metrics"]["thermal_noise_rms_nm"] > 0.0


def test_api_provenance(client):
    response = client.get("/api/provenance")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) >= 10
    assert len(data["edges"]) >= 10


def test_api_models(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert len(data["models"]) == 4


def test_api_discriminator(client):
    response = client.get("/api/discriminator")
    assert response.status_code == 200
    data = response.json()
    assert "optimal_experiment_design" in data
