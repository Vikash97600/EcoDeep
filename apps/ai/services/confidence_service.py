import math
from typing import List
from apps.ai.models import AIPredictionModel

class ConfidenceService:
    """Estimates empirical prediction confidence scores (0.0 to 100.0%) for AI inferences."""

    @staticmethod
    def calculate_prediction_confidence(model: AIPredictionModel, feature_vector: List[float]) -> float:
        """Computes empirical confidence index factoring in model R^2 and distance to feature centroid."""
        if not model:
            return 50.0

        base_r2 = max(0.5, model.r2_score)

        # Baseline expected feature mean vector [log_loc=4.3, deps=2.0, pop=0.2, cat=1.0, lang=1.0, ver=1.0]
        centroid = [4.3, 2.0, 0.2, 1.0, 1.0, 1.0]
        dist_sq = sum((f - c) ** 2 for f, c in zip(feature_vector, centroid))
        euclidean_dist = math.sqrt(dist_sq)

        # Distance penalty exponential decay
        distance_factor = math.exp(-0.15 * euclidean_dist)

        # Model accuracy factor (penalizes high MAPE)
        accuracy_factor = max(0.5, 1.0 - (model.mape / 100.0))

        raw_confidence = 100.0 * base_r2 * distance_factor * accuracy_factor
        return round(min(98.5, max(35.0, raw_confidence)), 1)
