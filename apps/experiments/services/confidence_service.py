class ConfidenceService:
    """Computes empirical confidence indices and data quality scores for benchmark experiments."""

    @staticmethod
    def calculate_confidence_index(sample_size: int, cv_percent: float, outlier_count: int, total_observations: int) -> float:
        """Calculates experimental confidence index (0.0 to 100.0%)."""
        if total_observations == 0 or sample_size == 0:
            return 0.0

        # Sample size factor (saturates at 30 iterations for CLT)
        size_factor = min(1.0, sample_size / 30.0)

        # Variance stability factor (penalizes CV > 15%)
        cv_factor = max(0.0, 1.0 - (cv_percent / 50.0))

        # Outlier resilience factor
        outlier_ratio = outlier_count / total_observations
        outlier_factor = max(0.0, 1.0 - outlier_ratio)

        confidence = 100.0 * (size_factor * 0.4 + cv_factor * 0.35 + outlier_factor * 0.25)
        return round(min(100.0, max(0.0, confidence)), 2)

    @staticmethod
    def calculate_data_quality_score(passed_rules: int, total_rules: int) -> float:
        """Calculates percentage compliance with integrity validation rules."""
        if total_rules == 0:
            return 100.0
        return round((passed_rules / total_rules) * 100.0, 2)
