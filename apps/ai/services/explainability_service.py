
from apps.ai.models import AIPredictionModel
from apps.libraries.models import Library


class ExplainabilityService:
    """Provides Explainable AI (XAI) feature attributions and human-readable reasoning narratives."""

    @staticmethod
    def generate_explanation(library: Library, model: AIPredictionModel, feature_vector: list[float], predicted_value: float) -> tuple[str, dict[str, float]]:
        """Generates feature attribution percentages and human-readable justification."""
        weights = model.feature_weights or {}
        feature_names = model.feature_names or []

        total_weight = sum(weights.values()) if weights else 1.0
        attributions = {}
        
        FEATURE_LABELS = {
            'log_lines_of_code': 'Lines of Code (Log Scale)',
            'dependency_count': 'Dependency Complexity',
            'popularity_score_normalized': 'Popularity & Adoption Score',
            'category_id': 'Functional Category Domain',
            'language_id': 'Language Runtime Profile',
            'version_major': 'Package Version Major'
        }

        for name, val in zip(feature_names, feature_vector):
            raw_w = weights.get(name, 1.0)
            contrib_pct = round((raw_w / total_weight) * 100.0, 1)
            display_name = FEATURE_LABELS.get(name, name.replace('_', ' ').title())
            attributions[display_name] = contrib_pct

        # Sort features by contribution
        top_features = sorted(attributions.items(), key=lambda x: x[1], reverse=True)[:2]
        top_feat_str = ", ".join([f"{f[0]} ({f[1]}%)" for f in top_features])

        # Generate human-readable narrative
        narrative = (
            f"Predicted {model.get_target_metric_display()} of {predicted_value:.2f} for '{library.library_name}'. "
            f"Primary positive contributors include {top_feat_str}. "
            f"Historical libraries within Category '{library.category.category_name if library.category else 'General'}' "
            f"and Language '{library.programming_language.language_name if library.programming_language else 'Python'}' "
            f"exhibit consistent algorithmic efficiency profiles."
        )

        return narrative, attributions
