import math
import numpy as np
from apps.recommendation.services.strategies.base import BaseScoringStrategy

class TopsisStrategy(BaseScoringStrategy):
    """TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) MCDM strategy."""

    @property
    def name(self) -> str:
        return 'TOPSIS'

    def compute_scores(self, normalized_matrix, weight_dict) -> dict:
        if not normalized_matrix:
            return {}

        res_ids = list(normalized_matrix.keys())
        metrics_keys = ['execution_time', 'cpu_usage', 'peak_memory', 'energy', 'co2']

        # Construct weighted matrix V
        v_matrix = {res_id: [] for res_id in res_ids}
        for res_id in res_ids:
            for k in metrics_keys:
                w_key = f"weight_{k}"
                weight = float(weight_dict.get(w_key, 0.20))
                v_matrix[res_id].append(weight * normalized_matrix[res_id][k])

        # Determine Ideal Solution A+ (max) and Negative Ideal A- (min)
        cols = zip(*[v_matrix[rid] for rid in res_ids])
        a_plus = [max(col) for col in cols]
        cols = zip(*[v_matrix[rid] for rid in res_ids])
        a_minus = [min(col) for col in cols]

        scores = {}
        for res_id in res_ids:
            v_vec = v_matrix[res_id]
            d_plus = math.sqrt(sum((v_vec[j] - a_plus[j]) ** 2 for j in range(len(metrics_keys))))
            d_minus = math.sqrt(sum((v_vec[j] - a_minus[j]) ** 2 for j in range(len(metrics_keys))))

            if (d_plus + d_minus) == 0:
                scores[res_id] = 0.5
            else:
                closeness = d_minus / (d_plus + d_minus)
                scores[res_id] = round(closeness, 4)

        return scores
