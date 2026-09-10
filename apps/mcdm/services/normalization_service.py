import math


class NormalizationService:
    """Provides vector, min-max, and linear cost/benefit normalization for MCDM decision matrices."""

    CRITERIA_KEYS = ['energy_joules', 'execution_time_ms', 'cpu_utilization_pct', 'ram_rss_mb', 'co2_emissions_g']

    @staticmethod
    def vector_normalize(matrix: list[dict[str, float]]) -> list[dict[str, float]]:
        """Applies Euclidean vector normalization: r_ij = x_ij / sqrt(sum(x_kj^2))."""
        if not matrix:
            return []

        # Compute column denominators
        denominators = {}
        for k in NormalizationService.CRITERIA_KEYS:
            sum_sq = sum(row.get(k, 0.0) ** 2 for row in matrix)
            denominators[k] = math.sqrt(sum_sq) if sum_sq > 0 else 1.0

        normalized_matrix = []
        for row in matrix:
            norm_row = {'library_id': row.get('library_id'), 'library_name': row.get('library_name')}
            for k in NormalizationService.CRITERIA_KEYS:
                norm_row[k] = round(row.get(k, 0.0) / denominators[k], 5)
            normalized_matrix.append(norm_row)

        return normalized_matrix

    @staticmethod
    def min_max_cost_normalize(matrix: list[dict[str, float]]) -> list[dict[str, float]]:
        """Applies linear cost normalization where lower is better: r_ij = min_j / x_ij."""
        if not matrix:
            return []

        mins = {}
        for k in NormalizationService.CRITERIA_KEYS:
            vals = [row.get(k, 0.0) for row in matrix if row.get(k, 0.0) > 0]
            mins[k] = min(vals) if vals else 1.0

        normalized = []
        for row in matrix:
            norm_row = {'library_id': row.get('library_id'), 'library_name': row.get('library_name')}
            for k in NormalizationService.CRITERIA_KEYS:
                val = row.get(k, 0.0)
                norm_row[k] = round(mins[k] / val, 5) if val > 0 else 1.0
            normalized.append(norm_row)

        return normalized
