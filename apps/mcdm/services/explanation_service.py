
class ExplanationService:
    """Generates transparent, human-readable explainable AI justifications for MCDM ranking decisions."""

    @staticmethod
    def generate_ranking_explanation(library_name: str, rank: int, green_score: float, profile_name: str, best_metric: str, metric_summary: dict[str, float]) -> str:
        """Generates plain-language explanation of multi-criteria ranking trade-offs."""
        if rank == 1:
            return (
                f"'{library_name}' ranked #1 with a Green Score of {green_score:.1f}/100 under the '{profile_name}'. "
                f"It achieved the ideal Pareto-optimal trade-off by minimizing {best_metric.replace('_', ' ')} "
                f"while maintaining superior overall multi-criteria efficiency."
            )
        elif rank == 2:
            return (
                f"'{library_name}' ranked #2 with a Green Score of {green_score:.1f}/100. "
                f"It represents a competitive green alternative with strong {best_metric.replace('_', ' ')} efficiency."
            )
        else:
            return (
                f"'{library_name}' ranked #{rank} with a Green Score of {green_score:.1f}/100. "
                f"Higher resource consumption in {best_metric.replace('_', ' ')} contributed to a lower closeness coefficient."
            )
