from apps.libraries.models import Library
from apps.xai.models import RecommendationExplanation, ExplanationTypeChoices, PersonaTypeChoices

class WhyNotService:
    """Generates contrastive 'Why-Not' explanations explaining why a specific candidate was not ranked #1."""

    @staticmethod
    def explain_why_not(
        unrecommended_lib: Library,
        winning_lib: Library,
        score_diff: float,
        bottleneck_metric: str = "energy_joules",
        persona: str = PersonaTypeChoices.DEVELOPER
    ) -> RecommendationExplanation:
        """Generates contrastive reasoning detailing specific metric deficits."""
        summary = f"'{unrecommended_lib.library_name}' was not ranked #1 due to higher {bottleneck_metric.replace('_', ' ')} consumption."
        
        narrative = (
            f"While '{unrecommended_lib.library_name}' is a valid functional dependency within '{unrecommended_lib.category.category_name if unrecommended_lib.category else 'General'}', "
            f"it was deprioritized against '{winning_lib.library_name}' (-{score_diff:.1f} Green Score points). "
            f"Specifically, '{unrecommended_lib.library_name}' drew higher {bottleneck_metric.replace('_', ' ')} and greater carbon intensity "
            f"under the active multi-criteria decision profile."
        )

        return RecommendationExplanation.objects.create(
            library=unrecommended_lib,
            category=unrecommended_lib.category,
            explanation_type=ExplanationTypeChoices.WHY_NOT_RECOMMENDED,
            persona=persona,
            summary_text=summary,
            detailed_narrative=narrative,
            confidence_score=94.5
        )
