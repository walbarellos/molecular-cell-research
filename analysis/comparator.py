"""Comparador formal entre Observacoes Empiricas (L2/L3) e Predicoes Sinteticas (L5)."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from domain import Observation, Prediction
from analysis.metrics import calculate_reproduction_metrics


class PointComparison(BaseModel):
    """Comparacao ponto a ponto sob condicoes identicas."""
    model_config = ConfigDict(frozen=True)

    condition_atp_uM: float
    condition_load_pN: float
    observed_value: float
    observed_uncertainty: float
    predicted_value: float
    residual: float
    z_score: float
    consistent_at_2sigma: bool


class ComparisonReport(BaseModel):
    """Relatorio formal consolidado de confronto observacao vs. predicao."""
    model_config = ConfigDict(frozen=True)

    model_id: str
    simulation_id: str
    target_property: str
    point_comparisons: List[PointComparison]
    metrics: Dict[str, Any]
    verdict: str
    verdict_rationale: str


def compare_observations_and_predictions(
    observations: List[Observation],
    predictions: List[Prediction],
    model_id: str,
    simulation_id: str,
    tolerance_2sigma_ratio: float = 0.90,
) -> ComparisonReport:
    """Cruza observacoes e predicoes baseando-se nas condicoes experimentais de contorno."""

    # Mapeia predicoes por condicao (atp_concentration_uM, load_force_pN)
    pred_map = {}
    for p in predictions:
        atp = float(p.conditions.get("atp_concentration_uM", 0.0))
        load = float(p.conditions.get("load_force_pN", 0.0))
        # Chave arredondada para tolerancia numerica
        key = (round(atp, 4), round(load, 4))
        pred_map[key] = p

    points: List[PointComparison] = []
    obs_vals = []
    pred_vals = []
    unc_vals = []

    for obs in observations:
        mea = obs.measurements[0]
        atp = float(mea.conditions.get("atp_concentration_uM", 0.0))
        load = float(mea.conditions.get("load_force_pN", 0.0))
        key = (round(atp, 4), round(load, 4))

        if key not in pred_map:
            raise KeyError(f"Predicao nao encontrada para condicao: atp={atp}, load={load}")

        pred = pred_map[key]
        y_obs = float(mea.quantity.value)
        sigma = float(mea.quantity.uncertainty) if mea.quantity.uncertainty else 0.02
        y_pred = float(pred.quantity.value)

        residual = y_obs - y_pred
        z_score = residual / sigma if sigma > 0 else 0.0
        consistent = abs(z_score) <= 2.0

        point = PointComparison(
            condition_atp_uM=atp,
            condition_load_pN=load,
            observed_value=round(y_obs, 5),
            observed_uncertainty=round(sigma, 5),
            predicted_value=round(y_pred, 5),
            residual=round(residual, 5),
            z_score=round(z_score, 4),
            consistent_at_2sigma=consistent,
        )
        points.append(point)

        obs_vals.append(y_obs)
        pred_vals.append(y_pred)
        unc_vals.append(sigma)

    metrics = calculate_reproduction_metrics(
        observed_values=obs_vals,
        predicted_values=pred_vals,
        uncertainties=unc_vals,
        degrees_of_freedom_param_count=2,
    )

    ratio_2s = metrics["within_2_sigma_ratio"]
    r2 = metrics["r_squared"]

    if ratio_2s >= tolerance_2sigma_ratio and r2 >= 0.95:
        verdict = "REPRODUCED_CONSISTENT"
        rationale = (
            f"O modelo reproduz os dados experimentais com sucesso: {metrics['within_2_sigma_count']}/{metrics['sample_count']} "
            f"pontos ({ratio_2s*100:.1f}%) estao dentro do intervalo de 2 sigma experimental, com R2 = {r2:.4f} e chi2_red = {metrics['chi2_reduced']:.3f}."
        )
    elif r2 >= 0.80:
        verdict = "MARGINAL_AGREEMENT"
        rationale = f"Aderencia parcial: R2 = {r2:.4f}, mas dispersao residual excede a tolerancia estatistica esperada."
    else:
        verdict = "DIVERGENT"
        rationale = f"Divergencia sistematica detectada: R2 = {r2:.4f}, max_z = {metrics['max_z_score']}."

    return ComparisonReport(
        model_id=model_id,
        simulation_id=simulation_id,
        target_property="velocity",
        point_comparisons=points,
        metrics=metrics,
        verdict=verdict,
        verdict_rationale=rationale,
    )
