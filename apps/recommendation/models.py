from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimeStampedModel
from apps.libraries.models import Library
from apps.benchmark.models import BenchmarkResult

class RecommendationStatusChoices(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active Recommendation'
    SUPERSEDED = 'SUPERSEDED', 'Superseded by New Benchmark'
    REJECTED = 'REJECTED', 'Flagged by Admin'


class Recommendation(TimeStampedModel):
    """Calculated recommendation mapping a baseline package to an energy-efficient alternative."""
    selected_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='recommendations_as_baseline')
    recommended_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='recommendations_as_replacement')
    benchmark_result = models.ForeignKey(BenchmarkResult, on_delete=models.SET_NULL, null=True, blank=True)
    energy_saved = models.DecimalField(max_digits=10, decimal_places=4, help_text="Absolute Joules saved per operation")
    percentage_saved = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage energy reduction (e.g. 68.50%)")
    recommendation_reason = models.TextField(help_text="Narrative explanation of energy savings and trade-offs")
    confidence_score = models.DecimalField(max_digits=4, decimal_places=2, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], default=0.95)
    status = models.CharField(max_length=20, choices=RecommendationStatusChoices.choices, default=RecommendationStatusChoices.ACTIVE)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Library Recommendation"
        verbose_name_plural = "Library Recommendations"
        ordering = ['-percentage_saved']

    def __str__(self):
        return f"Replace {self.selected_library.library_name} with {self.recommended_library.library_name} ({self.percentage_saved}% Greener)"


class RecommendationHistory(models.Model):
    """Tracks user feedback and interaction history with recommendations."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_history')
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name='user_interactions')
    accepted = models.BooleanField(default=False, help_text="User accepted and applied recommendation")
    rejected = models.BooleanField(default=False, help_text="User rejected recommendation")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Recommendation History"
        verbose_name_plural = "Recommendation Histories"
        ordering = ['-timestamp']

    def __str__(self):
        action = "Accepted" if self.accepted else ("Rejected" if self.rejected else "Viewed")
        return f"{self.user.username} {action} Rec #{self.recommendation.id}"
