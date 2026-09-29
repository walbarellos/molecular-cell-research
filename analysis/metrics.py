"""Metricas estatisticas formais para confronto entre dados observados e predicoes."""

from typing import Dict, List
import numpy as np


def calculate_reproduction_metrics(
    observed_values: List[float],
    predicted_values: List[float],
    uncertainties: List[float],
    degrees_of_freedom_param_count: int = 2,
) -> Dict[str, any]:
    """Calcula metricas estatisticas de aderencia e reproducibilidade."""
    if len(observed_values) != len(predicted_values) or len(observed_values) != len(uncertainties):
        raise ValueError("Vetores de observacao, predicao e incerteza devem ter o mesmo comprimento.")

    n = len(observed_values)
    if n == 0:
        raise ValueError("Vetores de entrada nao podem ser vazios.")

    y_obs = np.array(observed_values, dtype=np.float64)
    y_pred = np.array(predicted_values, dtype=np.float64)
    sigmas = np.array(uncertainties, dtype=np.float64)

    # Evita divisao por zero
    sigmas = np.where(sigmas <= 0, 1e-4, sigmas)

    residuals = y_obs - y_pred
    z_scores = residuals / sigmas

    rmse = float(np.sqrt(np.mean(residuals**2)))
    mae = float(np.mean(np.abs(residuals)))

    ss_res = float(np.sum(residuals**2))
    ss_tot = float(np.sum((y_obs - np.mean(y_obs))**2))
    r_squared = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 1.0

    dof = max(1, n - degrees_of_freedom_param_count)
    chi2_red = float(np.sum(z_scores**2) / dof)

    within_1_sigma = int(np.sum(np.abs(z_scores) <= 1.0))
    within_2_sigma = int(np.sum(np.abs(z_scores) <= 2.0))
    max_z = float(np.max(np.abs(z_scores)))

    return {
        "sample_count": n,
        "rmse": round(rmse, 6),
        "mae": round(mae, 6),
        "r_squared": round(r_squared, 6),
        "chi2_reduced": round(chi2_red, 4),
        "residuals": [round(float(r), 6) for r in residuals],
        "z_scores": [round(float(z), 4) for z in z_scores],
        "within_1_sigma_count": within_1_sigma,
        "within_1_sigma_ratio": round(within_1_sigma / n, 4),
        "within_2_sigma_count": within_2_sigma,
        "within_2_sigma_ratio": round(within_2_sigma / n, 4),
        "max_z_score": round(max_z, 4),
    }
