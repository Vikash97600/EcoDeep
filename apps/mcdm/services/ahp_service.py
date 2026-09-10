
class AHPService:
    """Implements Analytic Hierarchy Process (AHP) pairwise matrix weight derivation and consistency checking."""

    # Random Inconsistency Index (RI) table for matrix sizes 1 to 10
    RI_TABLE = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
    CRITERIA = ['energy_joules', 'execution_time_ms', 'cpu_utilization_pct', 'ram_rss_mb', 'co2_emissions_g']

    @staticmethod
    def get_default_ahp_matrix() -> list[list[float]]:
        """Returns standard research pairwise comparison matrix (5x5).
        Energy is preferred 2x over Latency, 3x over CPU/RAM, 4x over CO2."""
        return [
            [1.0, 2.0, 3.0, 3.0, 4.0],  # Energy
            [0.5, 1.0, 2.0, 2.0, 3.0],  # Latency
            [0.333, 0.5, 1.0, 1.0, 2.0], # CPU
            [0.333, 0.5, 1.0, 1.0, 2.0], # RAM
            [0.25, 0.333, 0.5, 0.5, 1.0] # CO2
        ]

    @staticmethod
    def calculate_ahp_weights(matrix: list[list[float]]) -> tuple[dict[str, float], float, float, bool]:
        """Calculates normalized priority weights, Consistency Index (CI), and Consistency Ratio (CR)."""
        n = len(matrix)
        
        # 1. Geometric Mean row calculation (Eigenvector approximation)
        geo_means = []
        for row in matrix:
            prod = 1.0
            for val in row:
                prod *= val
            geo_means.append(prod ** (1.0 / n))

        sum_geo = sum(geo_means)
        weights_list = [g / sum_geo for g in geo_means]

        # 2. Compute lambda_max for consistency validation
        # Multiply matrix by weight vector
        weighted_sums = []
        for i in range(n):
            row_sum = sum(matrix[i][j] * weights_list[j] for j in range(n))
            weighted_sums.append(row_sum / weights_list[i])

        lambda_max = sum(weighted_sums) / n

        # 3. Consistency Index (CI) and Consistency Ratio (CR)
        ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
        ri = AHPService.RI_TABLE.get(n, 1.12)
        cr = (ci / ri) if ri > 0 else 0.0
        is_consistent = cr < 0.10

        weights_dict = {AHPService.CRITERIA[i]: round(weights_list[i], 4) for i in range(min(n, len(AHPService.CRITERIA)))}
        return weights_dict, round(ci, 4), round(cr, 4), is_consistent
