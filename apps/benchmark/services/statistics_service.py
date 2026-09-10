import math

import numpy as np


class StatisticalAnalysisService:
    """Calculates descriptive and inferential statistics over benchmark sample distributions."""

    @staticmethod
    def filter_outliers_iqr(samples):
        if not samples or len(samples) < 4:
            return samples, []

        q1 = np.percentile(samples, 25)
        q3 = np.percentile(samples, 75)
        iqr = q3 - q1

        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        valid_samples = [s for s in samples if lower_bound <= s <= upper_bound]
        outliers = [s for s in samples if s < lower_bound or s > upper_bound]

        return valid_samples, outliers

    @staticmethod
    def calculate_statistics(samples):
        if not samples:
            return {}

        valid_samples, outliers = StatisticalAnalysisService.filter_outliers_iqr(samples)
        n = len(valid_samples)
        mean_val = np.mean(valid_samples) if n > 0 else 0.0
        std_dev = np.std(valid_samples, ddof=1) if n > 1 else 0.0

        margin_of_error = (1.96 * (std_dev / math.sqrt(n))) if n > 0 else 0.0

        return {
            'total_samples': len(samples),
            'valid_samples_count': n,
            'outliers_count': len(outliers),
            'min_ms': round(float(np.min(valid_samples)) / 1e6, 4) if n > 0 else 0.0,
            'max_ms': round(float(np.max(valid_samples)) / 1e6, 4) if n > 0 else 0.0,
            'mean_ms': round(float(mean_val) / 1e6, 4),
            'median_ms': round(float(np.median(valid_samples)) / 1e6, 4) if n > 0 else 0.0,
            'std_dev_ms': round(float(std_dev) / 1e6, 4),
            'variance': round(float(np.var(valid_samples, ddof=1)) / 1e12, 6) if n > 1 else 0.0,
            'ci_95_margin_ms': round(float(margin_of_error) / 1e6, 4),
            'ci_95_lower_ms': round(float(mean_val - margin_of_error) / 1e6, 4),
            'ci_95_upper_ms': round(float(mean_val + margin_of_error) / 1e6, 4),
        }
