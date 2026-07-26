class RecommendationConfidenceService:
    """Calculates statistical confidence score (0.000 - 1.000) for a recommendation."""

    @staticmethod
    def calculate_confidence(candidate_result):
        samples_count = candidate_result.raw_samples.count()
        iterations = candidate_result.iterations

        if samples_count >= 50 and iterations >= 50:
            return 0.980
        elif samples_count >= 20:
            return 0.920
        elif samples_count >= 10:
            return 0.850
        else:
            return 0.750
