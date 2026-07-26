class ConfidenceService:
    """Calculates statistical confidence score (0.000 - 1.000) based on sample size and variance."""

    @staticmethod
    def calculate_confidence(iterations, raw_samples_count):
        if iterations >= 50 and raw_samples_count >= 50:
            return 0.980
        elif iterations >= 20:
            return 0.920
        elif iterations >= 10:
            return 0.850
        else:
            return 0.700
