import math

from apps.recommendation.services.strategies.base import BaseScoringStrategy


class WeightedProductStrategy(BaseScoringStrategy):
    """Weighted Product Model (WPM) MCDM scoring strategy."""

    @property
    def name(self) -> str:
        return 'WPM'

    def compute_scores(self, normalized_matrix, weight_dict) -> dict:
        scores = {}
        for res_id, norm_metrics in normalized_matrix.items():
            product_score = 1.0
            for metric, norm_val in norm_metrics.items():
                w_key = f"weight_{metric}"
                weight = float(weight_dict.get(w_key, 0.20))
                # Avoid log(0) or 0^w edge cases
                safe_val = max(norm_val, 1e-4)
                product_score *= math.pow(safe_val, weight)
            scores[res_id] = round(product_score, 4)
        return scores
