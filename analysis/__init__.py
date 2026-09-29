"""Pacote de analise cientifica, comparacao e validacao (L6)."""

from analysis.metrics import calculate_reproduction_metrics
from analysis.comparator import compare_observations_and_predictions, PointComparison, ComparisonReport
from analysis.discriminator import (
    evaluate_discriminatory_grid,
    design_optimal_discriminatory_experiment,
    CandidateConditionEvaluation,
)

__all__ = [
    "calculate_reproduction_metrics",
    "compare_observations_and_predictions",
    "PointComparison",
    "ComparisonReport",
    "evaluate_discriminatory_grid",
    "design_optimal_discriminatory_experiment",
    "CandidateConditionEvaluation",
]
