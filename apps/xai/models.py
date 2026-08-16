from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, StatusChoices
from apps.libraries.models import Library, Category

class ExplanationTypeChoices(models.TextChoices):
    WHY_RECOMMENDED = 'WHY_RECOMMENDED', 'Why Recommended (Positive Justification)'
    WHY_NOT_RECOMMENDED = 'WHY_NOT_RECOMMENDED', 'Why Not Recommended (Contrastive Analysis)'
    COMPARATIVE = 'COMPARATIVE', 'Head-to-Head Comparative Trade-off'
    COUNTERFACTUAL = 'COUNTERFACTUAL', 'Counterfactual "What-If" Scenario'
    SHAP_ATTRIBUTION = 'SHAP_ATTRIBUTION', 'SHAP Feature Attribution Decomposition'
    DECISION_TRACE = 'DECISION_TRACE', 'Full Decision Lineage & Traceability'


class PersonaTypeChoices(models.TextChoices):
    DEVELOPER = 'DEVELOPER', 'Software Developer (Latency & Memory Focus)'
    RESEARCHER = 'RESEARCHER', 'Scientific Researcher (Confidence & p-value Focus)'
    ARCHITECT = 'ARCHITECT', 'Enterprise Architect (Reliability & Trade-offs)'
    ESG_MANAGER = 'ESG_MANAGER', 'Sustainability / ESG Manager (Carbon & Energy Focus)'


class RecommendationExplanation(TimeStampedModel):
    """Stores structured natural language explanations generated for recommendations."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='xai_explanations')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='xai_explanations')
    explanation_type = models.CharField(max_length=30, choices=ExplanationTypeChoices.choices, default=ExplanationTypeChoices.WHY_RECOMMENDED)
    persona = models.CharField(max_length=30, choices=PersonaTypeChoices.choices, default=PersonaTypeChoices.DEVELOPER)
    
    summary_text = models.CharField(max_length=255, help_text="One-sentence executive summary")
    detailed_narrative = models.TextField(help_text="Complete paragraph-length explainable AI rationale")
    confidence_score = models.FloatField(default=95.0, help_text="Explanation fidelity confidence (0-100%)")

    class Meta:
        verbose_name = "Recommendation Explanation"
        verbose_name_plural = "Recommendation Explanations"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_explanation_type_display()}] {self.library.library_name} ({self.persona})"


class FeatureContribution(TimeStampedModel):
    """Tracks individual criterion contribution weights towards a recommendation decision."""
    explanation = models.ForeignKey(RecommendationExplanation, on_delete=models.CASCADE, related_name='feature_contributions')
    feature_name = models.CharField(max_length=50, help_text="e.g. energy_joules, execution_time_ms, ram_rss_mb")
    raw_value = models.FloatField(help_text="Observed physical metric value")
    contribution_score = models.FloatField(help_text="Calculated marginal contribution weight")
    percentage_impact = models.FloatField(help_text="Relative percentage impact (0-100%)")
    is_positive = models.BooleanField(default=True, help_text="True if this feature helped the library rank higher")

    class Meta:
        verbose_name = "Feature Contribution"
        verbose_name_plural = "Feature Contributions"
        ordering = ['-percentage_impact']


class SHAPAttributionResult(TimeStampedModel):
    """Stores local and global SHAP (Shapley Additive Explanations) feature attributions."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='shap_results')
    base_value = models.FloatField(default=50.0, help_text="Expected baseline Green Score")
    shap_values_json = models.JSONField(default=dict, help_text="Dictionary of feature SHAP values phi_i")
    top_contributing_features = models.JSONField(default=list)

    class Meta:
        verbose_name = "SHAP Attribution Result"
        verbose_name_plural = "SHAP Attribution Results"
        ordering = ['-created_at']


class CounterfactualScenario(TimeStampedModel):
    """Stores 'what-if' counterfactual simulations detailing minimum changes needed for rank reversal."""
    target_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='counterfactuals')
    hypothetical_condition = models.CharField(max_length=255, help_text="e.g. Reduce CPU consumption by 15%")
    resulting_rank = models.PositiveIntegerField(help_text="Projected rank position if condition met")
    resulting_green_score = models.FloatField(help_text="Projected new Green Score")
    is_feasible = models.BooleanField(default=True)
    narrative = models.TextField()

    class Meta:
        verbose_name = "Counterfactual Scenario"
        verbose_name_plural = "Counterfactual Scenarios"
        ordering = ['-created_at']


class DecisionTraceAudit(TimeStampedModel):
    """Audit log capturing end-to-end decision lineage from physical sensors to recommendation."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='decision_traces')
    benchmark_runs_count = models.PositiveIntegerField(default=1)
    weight_profile_used = models.CharField(max_length=100)
    mcdm_solver_used = models.CharField(max_length=50, default='TOPSIS')
    carbon_grid_used = models.CharField(max_length=100)
    trace_hash_sha256 = models.CharField(max_length=64, help_text="SHA256 integrity fingerprint")
    lineage_metadata = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Decision Trace Audit"
        verbose_name_plural = "Decision Trace Audits"
        ordering = ['-created_at']


class TrustScoreRecord(TimeStampedModel):
    """Composite Trust Score evaluating recommendation completeness, fidelity, and clarity."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='trust_scores')
    overall_trust_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    data_completeness_score = models.FloatField(default=95.0)
    measurement_fidelity_score = models.FloatField(default=98.0)
    explanation_clarity_score = models.FloatField(default=92.0)
    status_badge = models.CharField(max_length=30, default='High Trust (Verified)')

    class Meta:
        verbose_name = "Trust Score Record"
        verbose_name_plural = "Trust Score Records"
        ordering = ['-overall_trust_score']
