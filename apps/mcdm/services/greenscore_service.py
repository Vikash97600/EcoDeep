from typing import Dict, Any

class GreenScoreService:
    """Calculates unified calibrated Green Scores (0.0 to 100.0) with confidence bounds."""

    @staticmethod
    def calculate_calibrated_score(closeness_coefficient: float, confidence_index: float = 95.0) -> float:
        """Converts TOPSIS relative closeness C_i* to calibrated 0-100 scale."""
        raw_score = closeness_coefficient * 100.0
        return round(min(100.0, max(0.0, raw_score)), 2)

    @staticmethod
    def get_efficiency_badge(green_score: float) -> tuple[str, str]:
        """Returns CSS class and tier label for a Green Score."""
        if green_score >= 85.0:
            return 'bg-success', 'Tier A+ (Optimal Green)'
        elif green_score >= 70.0:
            return 'bg-primary', 'Tier A (High Efficiency)'
        elif green_score >= 50.0:
            return 'bg-warning text-dark', 'Tier B (Moderate Efficiency)'
        else:
            return 'bg-danger', 'Tier C (High Resource Consumption)'
