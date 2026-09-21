import numpy as np


class NormalizationService:
    """Applies continuous magnitude-preserving normalization to cost metrics where lower values are better."""

    # Physical baseline thresholds for single-candidate scaling
    BASELINES = {
        'execution_time': 50.0,   # ms
        'cpu_usage': 50.0,        # %
        'peak_memory': 64.0,      # MB
        'energy': 5.0,            # Joules
        'co2': 0.005              # grams
    }

    @staticmethod
    def normalize_results(results_data):
        """
        Input: List of dicts containing result_id, execution_time, cpu_usage, peak_memory, energy, co2.
        Output: Dict mapping result_id -> normalized_metrics_dict (values in 0.0 - 1.0, 1.0 is best).
        """
        if not results_data:
            return {}

        metrics_keys = ['execution_time', 'cpu_usage', 'peak_memory', 'energy', 'co2']
        matrix = {k: np.array([float(r[k]) for r in results_data]) for k in metrics_keys}

        normalized_output = {}
        candidate_count = len(results_data)

        for index, r in enumerate(results_data):
            res_id = r['result_id']
            norm_dict = {}
            for k in metrics_keys:
                arr = matrix[k]
                val = float(r[k])
                min_val, max_val = np.min(arr), np.max(arr)

                if candidate_count > 1 and max_val > min_val:
                    # Euclidean Vector Normalization for cost metrics (lower cost -> higher score)
                    # Preserves exact proportional magnitude differences across candidates
                    vec_norm = np.sqrt(np.sum(arr**2))
                    if vec_norm > 0:
                        norm_dict[k] = max(0.01, min(1.0, 1.0 - (val / (vec_norm * 1.05))))
                    else:
                        norm_dict[k] = 1.0
                else:
                    # Single candidate or identical candidates: scale against physical baseline threshold
                    b_val = NormalizationService.BASELINES.get(k, 1.0)
                    norm_dict[k] = max(0.05, min(1.0, 1.0 / (1.0 + (val / b_val))))

            normalized_output[res_id] = norm_dict

        return normalized_output
