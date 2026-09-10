from apps.libraries.models import Library
from apps.xai.models import (
    ExplanationTypeChoices,
    PersonaTypeChoices,
    RecommendationExplanation,
)


class ComparativeExplanationService:
    """Generates comparative trade-off explanations between two libraries."""

    @staticmethod
    def generate_comparison_explanation(lib_a: Library, lib_b: Library, delta_energy_pct: float, delta_latency_pct: float, persona: str = PersonaTypeChoices.DEVELOPER) -> RecommendationExplanation:
        """Generates trade-off narrative comparing execution time vs energy savings."""
        summary = f"Comparing '{lib_a.library_name}' vs '{lib_b.library_name}': {delta_energy_pct:.1f}% energy variance."
        
        narrative = (
            f"Head-to-head analysis between '{lib_a.library_name}' and '{lib_b.library_name}': "
            f"'{lib_b.library_name}' achieves {delta_energy_pct:.1f}% lower energy consumption (Joules) "
            f"and {delta_latency_pct:.1f}% faster latency per operation. "
            f"For latency-critical and energy-constrained deployments, migrating to '{lib_b.library_name}' offers Pareto-optimal efficiency."
        )

        return RecommendationExplanation.objects.create(
            library=lib_b,
            category=lib_b.category,
            explanation_type=ExplanationTypeChoices.COMPARATIVE,
            persona=persona,
            summary_text=summary,
            detailed_narrative=narrative,
            confidence_score=96.0
        )
