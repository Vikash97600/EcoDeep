from django.db import models
from apps.core.models import TimeStampedModel
from apps.benchmark.models import BenchmarkResult, BenchmarkSession, BenchmarkTask
from apps.libraries.models import LibraryVersion

class ScoringStrategyChoices(models.TextChoices):
    WEIGHTED_SUM = 'WSM', 'Weighted Sum Model (WSM)'
    WEIGHTED_PRODUCT = 'WPM', 'Weighted Product Model (WPM)'
    TOPSIS = 'TOPSIS', 'TOPSIS (Ideal Solution Distance)'


class ScoreCategoryChoices(models.TextChoices):
    EXCELLENT = 'EXCELLENT', 'Excellent (90-100)'
    GOOD = 'GOOD', 'Good (70-89)'
    AVERAGE = 'AVERAGE', 'Average (50-69)'
    NEEDS_IMPROVEMENT = 'NEEDS_IMPROVEMENT', 'Needs Improvement (<50)'


class WeightProfile(TimeStampedModel):
    """Configuration profile storing metric weighting preferences for Green Score calculations."""
    profile_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    is_default = models.BooleanField(default=False)

    weight_execution_time = models.DecimalField(max_digits=5, decimal_places=4, default=0.30)
    weight_cpu_usage = models.DecimalField(max_digits=5, decimal_places=4, default=0.20)
    weight_peak_memory = models.DecimalField(max_digits=5, decimal_places=4, default=0.20)
    weight_energy = models.DecimalField(max_digits=5, decimal_places=4, default=0.20)
    weight_co2 = models.DecimalField(max_digits=5, decimal_places=4, default=0.10)

    class Meta:
        verbose_name = "Weight Profile"
        verbose_name_plural = "Weight Profiles"
        ordering = ['profile_name']

    def __str__(self):
        return self.profile_name


class GreenScore(TimeStampedModel):
    """Unified Green Score (0-100) calculated using Multi-Criteria Decision Making (MCDM)."""
    result = models.OneToOneField(BenchmarkResult, on_delete=models.CASCADE, related_name='green_score_record')
    library_version = models.ForeignKey(LibraryVersion, on_delete=models.CASCADE, related_name='green_scores')
    session = models.ForeignKey(BenchmarkSession, on_delete=models.CASCADE, related_name='green_scores')
    task = models.ForeignKey(BenchmarkTask, on_delete=models.CASCADE, related_name='green_scores')
    weight_profile = models.ForeignKey(WeightProfile, on_delete=models.CASCADE, related_name='green_scores')

    strategy_used = models.CharField(max_length=20, choices=ScoringStrategyChoices.choices, default=ScoringStrategyChoices.TOPSIS)
    score = models.DecimalField(max_digits=6, decimal_places=2, help_text="Green Score on a 0.00 - 100.00 scale")
    category = models.CharField(max_length=20, choices=ScoreCategoryChoices.choices, default=ScoreCategoryChoices.GOOD)
    confidence_score = models.DecimalField(max_digits=4, decimal_places=3, default=0.950, help_text="Statistical confidence score (0.000 - 1.000)")
    explanation = models.TextField(help_text="Human-readable score explanation text")

    class Meta:
        verbose_name = "Green Score"
        verbose_name_plural = "Green Scores"
        ordering = ['-score']
        indexes = [
            models.Index(fields=['score']),
            models.Index(fields=['library_version', 'task']),
        ]

    def __str__(self):
        return f"{self.library_version} - Green Score: {self.score}/100 ({self.category})"


class HistoricalGreenScore(TimeStampedModel):
    """Tracks historical evolution of Green Scores across package versions."""
    library_version = models.ForeignKey(LibraryVersion, on_delete=models.CASCADE, related_name='historical_scores')
    task = models.ForeignKey(BenchmarkTask, on_delete=models.CASCADE, related_name='historical_scores')
    score = models.DecimalField(max_digits=6, decimal_places=2)
    strategy_used = models.CharField(max_length=20, choices=ScoringStrategyChoices.choices)

    class Meta:
        verbose_name = "Historical Green Score"
        verbose_name_plural = "Historical Green Scores"
        ordering = ['-created_at']

    def __str__(self):
        return f"Historical {self.library_version}: {self.score}"
