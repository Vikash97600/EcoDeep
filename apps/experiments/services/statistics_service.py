import math
from typing import Any


class StatisticsService:
    """Computes descriptive summaries, parametric/non-parametric inferential statistics, and effect sizes."""

    @staticmethod
    def compute_descriptive_stats(values: list[float]) -> dict[str, float]:
        """Calculates comprehensive descriptive statistics for an empirical sample."""
        n = len(values)
        if n == 0:
            return {}

        sorted_vals = sorted(values)
        mean_val = sum(values) / n
        median_val = sorted_vals[n // 2] if n % 2 != 0 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0
        
        min_val = sorted_vals[0]
        max_val = sorted_vals[-1]
        range_val = max_val - min_val

        q1 = sorted_vals[int(n * 0.25)]
        q3 = sorted_vals[int(n * 0.75)]
        iqr_val = q3 - q1

        variance_val = sum((x - mean_val) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
        std_dev_val = math.sqrt(variance_val)
        cv_val = (std_dev_val / mean_val * 100.0) if mean_val > 0 else 0.0

        # Confidence intervals (t_crit approximation for alpha=0.05 and alpha=0.01)
        t_crit_95 = 2.045 if n >= 30 else 2.228  # conservative t-critical
        t_crit_99 = 2.750 if n >= 30 else 3.169
        
        margin_95 = t_crit_95 * (std_dev_val / math.sqrt(n)) if n > 0 else 0.0
        margin_99 = t_crit_99 * (std_dev_val / math.sqrt(n)) if n > 0 else 0.0

        return {
            'sample_size': n,
            'mean': round(mean_val, 4),
            'median': round(median_val, 4),
            'min_val': round(min_val, 4),
            'max_val': round(max_val, 4),
            'range_val': round(range_val, 4),
            'iqr': round(iqr_val, 4),
            'variance': round(variance_val, 6),
            'std_dev': round(std_dev_val, 4),
            'coefficient_of_variation': round(cv_val, 2),
            'ci_95_lower': round(mean_val - margin_95, 4),
            'ci_95_upper': round(mean_val + margin_95, 4),
            'ci_99_lower': round(mean_val - margin_99, 4),
            'ci_99_upper': round(mean_val + margin_99, 4),
        }

    @staticmethod
    def compute_two_sample_ttest(sample_a: list[float], sample_b: list[float]) -> dict[str, Any]:
        """Performs Student's two-sample independent t-test."""
        n_a, n_b = len(sample_a), len(sample_b)
        if n_a < 2 or n_b < 2:
            return {'t_stat': 0.0, 'p_value': 1.0, 'reject_null': False}

        mean_a = sum(sample_a) / n_a
        mean_b = sum(sample_b) / n_b

        var_a = sum((x - mean_a) ** 2 for x in sample_a) / (n_a - 1)
        var_b = sum((x - mean_b) ** 2 for x in sample_b) / (n_b - 1)

        pooled_se = math.sqrt((var_a / n_a) + (var_b / n_b))
        if pooled_se == 0:
            return {'t_stat': 0.0, 'p_value': 1.0, 'reject_null': False}

        t_stat = (mean_a - mean_b) / pooled_se
        df = n_a + n_b - 2
        
        # Approximate two-tailed p-value using normal distribution for larger df
        z = abs(t_stat)
        p_value = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))
        p_value = max(0.000001, min(1.0, p_value))

        return {
            't_stat': round(t_stat, 4),
            'p_value': round(p_value, 6),
            'degrees_of_freedom': df,
            'reject_null': p_value < 0.05
        }

    @staticmethod
    def compute_cohens_d(sample_a: list[float], sample_b: list[float]) -> dict[str, Any]:
        """Calculates Cohen's d effect size for parametric comparisons."""
        n_a, n_b = len(sample_a), len(sample_b)
        if n_a < 2 or n_b < 2:
            return {'d_value': 0.0, 'magnitude': 'Negligible'}

        mean_a = sum(sample_a) / n_a
        mean_b = sum(sample_b) / n_b

        var_a = sum((x - mean_a) ** 2 for x in sample_a) / (n_a - 1)
        var_b = sum((x - mean_b) ** 2 for x in sample_b) / (n_b - 1)

        pooled_sd = math.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
        if pooled_sd == 0:
            return {'d_value': 0.0, 'magnitude': 'Negligible'}

        d = (mean_a - mean_b) / pooled_sd
        abs_d = abs(d)

        if abs_d < 0.2:
            magnitude = 'Negligible'
        elif abs_d < 0.5:
            magnitude = 'Small'
        elif abs_d < 0.8:
            magnitude = 'Medium'
        else:
            magnitude = 'Large'

        return {'d_value': round(d, 4), 'magnitude': magnitude}

    @staticmethod
    def compute_cliffs_delta(sample_a: list[float], sample_b: list[float]) -> dict[str, Any]:
        """Calculates Cliff's Delta non-parametric effect size."""
        n_a, n_b = len(sample_a), len(sample_b)
        if n_a == 0 or n_b == 0:
            return {'delta': 0.0, 'magnitude': 'Negligible'}

        greater = sum(1 for x in sample_a for y in sample_b if x > y)
        less = sum(1 for x in sample_a for y in sample_b if x < y)

        delta = (greater - less) / (n_a * n_b)
        abs_delta = abs(delta)

        if abs_delta < 0.147:
            magnitude = 'Negligible'
        elif abs_delta < 0.33:
            magnitude = 'Small'
        elif abs_delta < 0.474:
            magnitude = 'Medium'
        else:
            magnitude = 'Large'

        return {'delta': round(delta, 4), 'magnitude': magnitude}
