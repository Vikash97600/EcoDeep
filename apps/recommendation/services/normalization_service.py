import numpy as np


class NormalizationService:
    """Applies Inverse Min-Max Normalization to cost metrics where lower values are better."""

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
        for index, r in enumerate(results_data):
            res_id = r['result_id']
            norm_dict = {}
            for k in metrics_keys:
                arr = matrix[k]
                min_val, max_val = np.min(arr), np.max(arr)
                
                if max_val == min_val:
                    norm_dict[k] = 1.0  # Equal baseline
                else:
                    # Inverse Min-Max Scaling (Lower Cost = Higher Score)
                    norm_dict[k] = (max_val - float(r[k])) / (max_val - min_val)
            normalized_output[res_id] = norm_dict

        return normalized_output
