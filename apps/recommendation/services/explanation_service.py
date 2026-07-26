class ExplanationService:
    """Generates human-readable natural language rationale for calculated Green Scores."""

    @staticmethod
    def generate_explanation(library_name, score, category, raw_result, weight_profile):
        return (
            f"Package '{library_name}' achieved a Green Score of {score}/100 ({category}) under the "
            f"'{weight_profile.profile_name}' weight profile. Performance metrics: Mean Latency: {raw_result.execution_time} ms, "
            f"Peak RAM: {raw_result.peak_memory} MB, CPU Utilization: {raw_result.average_cpu}%, "
            f"Physical Energy Consumed: {raw_result.energy} Joules, Carbon Emissions: {raw_result.co2} gCO2eq."
        )
