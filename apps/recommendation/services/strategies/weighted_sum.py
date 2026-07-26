from apps.recommendation.services.strategies.base import BaseScoringStrategy

class WeightedSumStrategy(BaseScoringStrategy):
    """Weighted Sum Model (WSM) MCDM scoring strategy."""

    @property
    def name(self) -> str:
        return 'WSM'

    def compute_scores(self, normalized_matrix, weight_dict) -> dict:
        scores = {}
        for res_id, norm_metrics in normalized_matrix.items():
            total_score = 0.0
            for metric, norm_val in norm_metrics.items():
                w_key = f"weight_{metric}"
                weight = float(weight_dict.get(w_key, 0.20))
                total_score += weight * norm_val
            scores[res_id] = round(total_score, 4)
        return scores
