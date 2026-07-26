class RecommendationExplanationService:
    """Generates Explainable AI (XAI) evidence text with exact metric percentage savings."""

    @staticmethod
    def generate_recommendation_explanation(target_result, candidate_result, profile_type):
        if not target_result or target_result.id == candidate_result.id:
            return (
                f"{candidate_result.library_version} achieved a Green Score of {candidate_result.green_score}/100 "
                f"on task '{candidate_result.task.task_name}' (Execution Time: {candidate_result.execution_time} ms, "
                f"Peak RAM: {candidate_result.peak_memory} MB, Energy: {candidate_result.energy} J)."
            )

        t_time = float(target_result.execution_time)
        c_time = float(candidate_result.execution_time)
        t_energy = float(target_result.energy)
        c_energy = float(candidate_result.energy)
        t_mem = float(target_result.peak_memory)
        c_mem = float(candidate_result.peak_memory)

        time_saved_pct = round(((t_time - c_time) / t_time) * 100, 1) if t_time > 0 else 0.0
        energy_saved_pct = round(((t_energy - c_energy) / t_energy) * 100, 1) if t_energy > 0 else 0.0
        mem_saved_pct = round(((t_mem - c_mem) / t_mem) * 100, 1) if t_mem > 0 else 0.0

        return (
            f"{candidate_result.library_version} is recommended as a greener replacement for {target_result.library_version}. "
            f"In benchmark evaluations on task '{candidate_result.task.task_name}', {candidate_result.library_version.library.library_name} "
            f"achieved a Green Score of {candidate_result.green_score}/100 compared to {target_result.green_score}/100. "
            f"Specifically, it executed {time_saved_pct}% faster ({c_time} ms vs {t_time} ms), "
            f"consumed {energy_saved_pct}% less energy ({c_energy} J vs {t_energy} J), "
            f"and required {mem_saved_pct}% less peak RAM ({c_mem} MB vs {t_mem} MB)."
        )
