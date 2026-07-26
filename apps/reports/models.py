from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel

class ReportTypeChoices(models.TextChoices):
    CATEGORY_SUMMARY = 'CATEGORY', 'Category Summary Report'
    LIBRARY_COMPARISON = 'COMPARISON', 'Side-by-Side Comparison Report'
    FULL_DATASET_EXPORT = 'DATASET', 'Full EcoLibBench Dataset Export'


class GeneratedReport(TimeStampedModel):
    """Tracks dynamically generated PDF and CSV report artifacts."""
    report_name = models.CharField(max_length=200)
    type = models.CharField(max_length=30, choices=ReportTypeChoices.choices, default=ReportTypeChoices.CATEGORY_SUMMARY)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_on = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='reports/pdf/', blank=True, null=True)
    csv_file = models.FileField(upload_to='reports/csv/', blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Generated Report"
        verbose_name_plural = "Generated Reports"
        ordering = ['-generated_on']

    def __str__(self):
        return f"{self.report_name} ({self.get_type_display()}) - {self.generated_on.strftime('%Y-%m-%d')}"
