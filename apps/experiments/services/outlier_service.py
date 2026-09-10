import math


class OutlierService:
    """Provides empirical outlier detection algorithms: IQR, Standard Z-Score, and Modified Z-Score (MAD)."""

    @staticmethod
    def detect_iqr_outliers(values: list[float]) -> list[bool]:
        """Detects outliers using standard Interquartile Range (IQR) rule: [Q1 - 1.5*IQR, Q3 + 1.5*IQR]."""
        if len(values) < 4:
            return [False] * len(values)

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[int(n * 0.25)]
        q3 = sorted_vals[int(n * 0.75)]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        return [val < lower_bound or val > upper_bound for val in values]

    @staticmethod
    def detect_zscore_outliers(values: list[float], threshold: float = 3.0) -> list[bool]:
        """Detects outliers using standard Z-Score: |x - mean| / std_dev > threshold."""
        n = len(values)
        if n < 3:
            return [False] * n

        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return [False] * n

        return [abs((x - mean) / std_dev) > threshold for x in values]

    @staticmethod
    def detect_mad_outliers(values: list[float], threshold: float = 3.5) -> list[bool]:
        """Detects outliers using Modified Z-Score based on Median Absolute Deviation (MAD)."""
        n = len(values)
        if n < 3:
            return [False] * n

        sorted_vals = sorted(values)
        median = sorted_vals[n // 2]
        
        deviations = sorted([abs(x - median) for x in values])
        mad = deviations[n // 2]

        if mad == 0:
            return [False] * n

        modified_z = [(0.6745 * abs(x - median)) / mad for x in values]
        return [score > threshold for score in modified_z]
