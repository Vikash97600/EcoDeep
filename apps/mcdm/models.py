from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel, StatusChoices
from apps.libraries.models import Library, Category
from apps.benchmark.models import BenchmarkTask

class MCDMMethodChoices(models.TextChoices):
    TOPSIS = 'TOPSIS', 'TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)'
    WSM = 'WSM', 'WSM (Weighted Sum Model)'
    WPM = 'WPM', 'WPM (Weighted Product Model)'
    AHP = 'AHP', 'AHP (Analytic Hierarchy Process)'
    HYBRID = 'HYBRID', 'Hybrid (AHP Weights + TOPSIS Distance)'


class ProfileTypeChoices(models.TextChoices):
    BALANCED = 'BALANCED', 'Balanced Decision Profile'
    ENERGY_FOCUSED = 'ENERGY_FOCUSED', 'Energy-First Profile'
    PERFORMANCE_FOCUSED = 'PERFORMANCE_FOCUSED', 'Low-Latency Performance Profile'
    MEMORY_FOCUSED = 'MEMORY_FOCUSED', 'Memory-Constrained Profile'
    CARBON_NEUTRAL = 'CARBON_NEUTRAL', 'Minimal Carbon Emissions Profile'
    CUSTOM = 'CUSTOM', 'Custom Stakeholder Defined Profile'


class MCDMWeightProfile(TimeStampedModel):
    """Stores configurable multi-criteria weighting distributions."""
    profile_name = models.CharField(max_length=100, unique=True)
    profile_type = models.CharField(max_length=30, choices=ProfileTypeChoices.choices, default=ProfileTypeChoices.BALANCED)
    
    # Normalized weights (Summing to 1.0)
    weight_energy = models.FloatField(default=0.35, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    weight_execution_time = models.FloatField(default=0.25, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    weight_cpu = models.FloatField(default=0.15, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    weight_memory = models.FloatField(default=0.15, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    weight_co2 = models.FloatField(default=0.10, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "MCDM Weight Profile"
        verbose_name_plural = "MCDM Weight Profiles"
        ordering = ['profile_name']

    def __str__(self):
        return f"{self.profile_name} ({self.get_profile_type_display()})"


class MCDMEvaluationRun(TimeStampedModel):
    """Audit log capturing a multi-criteria ranking computation."""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='mcdm_evaluations')
    benchmark_task = models.ForeignKey(BenchmarkTask, on_delete=models.SET_NULL, null=True, blank=True, related_name='mcdm_evaluations')
    weight_profile = models.ForeignKey(MCDMWeightProfile, on_delete=models.CASCADE, related_name='evaluation_runs')
    mcdm_method = models.CharField(max_length=30, choices=MCDMMethodChoices.choices, default=MCDMMethodChoices.TOPSIS)
    candidate_count = models.PositiveIntegerField(default=0)
    
    decision_matrix_json = models.JSONField(default=dict, help_text="Raw unnormalized decision matrix")
    normalized_matrix_json = models.JSONField(default=dict, help_text="Normalized decision matrix")
    ranking_results_json = models.JSONField(default=list, help_text="Ordered ranking output with scores")

    class Meta:
        verbose_name = "MCDM Evaluation Run"
        verbose_name_plural = "MCDM Evaluation Runs"
        ordering = ['-created_at']

    def __str__(self):
        return f"MCDM Run: {self.category.category_name} via {self.get_mcdm_method_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class GreenScoreRecord(TimeStampedModel):
    """Calculated Green Score for a specific library in an MCDM evaluation run."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='mcdm_green_scores')
    evaluation_run = models.ForeignKey(MCDMEvaluationRun, on_delete=models.CASCADE, related_name='green_score_records')
    
    green_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)], help_text="Calibrated 0-100 score")
    rank_position = models.PositiveIntegerField(help_text="Relative rank position (1 is best)")
    
    # Specific MCDM model metrics
    closeness_coefficient = models.FloatField(default=0.0, help_text="TOPSIS Relative Closeness C_i* (0.0 - 1.0)")
    wsm_score = models.FloatField(default=0.0)
    wpm_score = models.FloatField(default=0.0)
    confidence_score = models.FloatField(default=95.0, help_text="Confidence index based on sample consistency")
    
    explanation_text = models.TextField(help_text="Explainable AI narrative justification")

    class Meta:
        verbose_name = "Green Score Record"
        verbose_name_plural = "Green Score Records"
        ordering = ['rank_position']

    def __str__(self):
        return f"#{self.rank_position} {self.library.library_name} -> Green Score: {self.green_score:.1f}"


class SensitivityAuditReport(TimeStampedModel):
    """Stores sensitivity analysis results evaluating rank stability under weight perturbations."""
    evaluation_run = models.ForeignKey(MCDMEvaluationRun, on_delete=models.CASCADE, related_name='sensitivity_reports')
    perturbed_criterion = models.CharField(max_length=50)
    perturbation_pct = models.FloatField(help_text="Percentage change in criterion weight (+/- %)")
    rank_reversals_count = models.PositiveIntegerField(default=0)
    spearman_rho = models.FloatField(default=1.0, help_text="Spearman's rank correlation coefficient")
    is_robust = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Sensitivity Audit Report"
        verbose_name_plural = "Sensitivity Audit Reports"
        ordering = ['-created_at']


class AHPComparisonMatrix(TimeStampedModel):
    """Stores pairwise comparison matrices and Consistency Ratio validation for AHP."""
    profile = models.ForeignKey(MCDMWeightProfile, on_delete=models.CASCADE, related_name='ahp_matrices')
    matrix_json = models.JSONField(default=dict, help_text="5x5 Pairwise comparison matrix")
    consistency_index = models.FloatField(default=0.0)
    consistency_ratio = models.FloatField(default=0.0, help_text="CR = CI / RI (Must be < 0.10)")
    is_consistent = models.BooleanField(default=True)

    class Meta:
        verbose_name = "AHP Comparison Matrix"
        verbose_name_plural = "AHP Comparison Matrices"
