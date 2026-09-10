from django.contrib.auth.models import User
from django.db import models

from apps.benchmark.models import BenchmarkTask
from apps.core.models import TimeStampedModel
from apps.libraries.models import Library


class ExperimentStatusChoices(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft / Configured'
    RUNNING = 'RUNNING', 'In Execution'
    COMPLETED = 'COMPLETED', 'Completed & Validated'
    FAILED = 'FAILED', 'Execution / Validation Failed'


class OutlierMethodChoices(models.TextChoices):
    IQR = 'IQR', 'Interquartile Range (IQR)'
    Z_SCORE = 'Z_SCORE', 'Standard Z-Score (|Z| > 3.0)'
    MODIFIED_Z_SCORE = 'MODIFIED_Z_SCORE', 'Modified Z-Score / MAD (|M| > 3.5)'


class HypothesisTestChoices(models.TextChoices):
    STUDENT_T_TEST = 'STUDENT_T_TEST', "Student's Two-Sample Independent t-test"
    PAIRED_T_TEST = 'PAIRED_T_TEST', "Paired Sample t-test"
    MANN_WHITNEY_U = 'MANN_WHITNEY_U', "Mann-Whitney U Non-Parametric Test"
    WILCOXON_SIGNED_RANK = 'WILCOXON_SIGNED_RANK', "Wilcoxon Signed-Rank Test"


class ScientificExperiment(TimeStampedModel):
    """Defines a formal empirical research experiment with hypotheses and controls."""
    title = models.CharField(max_length=255)
    researcher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='experiments')
    research_question = models.TextField(help_text="Formal empirical research question")
    null_hypothesis = models.TextField(help_text="H0: Null hypothesis statement")
    alternative_hypothesis = models.TextField(help_text="H1: Alternative research hypothesis")
    
    benchmark_task = models.ForeignKey(BenchmarkTask, on_delete=models.CASCADE, related_name='experiments')
    candidate_libraries = models.ManyToManyField(Library, related_name='experiments')
    
    warmup_iterations = models.PositiveIntegerField(default=3, help_text="Discarded warm-up runs to stabilize JIT/cache")
    measurement_iterations = models.PositiveIntegerField(default=15, help_text="Measured repetitions for statistical power")
    cooldown_seconds = models.FloatField(default=1.0, help_text="Thermal stabilization cooldown between runs")
    random_seed = models.IntegerField(default=42, help_text="Deterministic seed for execution order randomization")
    
    outlier_method = models.CharField(max_length=30, choices=OutlierMethodChoices.choices, default=OutlierMethodChoices.IQR)
    alpha_threshold = models.FloatField(default=0.05, help_text="Significance level alpha for hypothesis testing")
    status = models.CharField(max_length=20, choices=ExperimentStatusChoices.choices, default=ExperimentStatusChoices.DRAFT)
    
    hardware_provenance = models.JSONField(default=dict, blank=True, help_text="CPU model, core count, RAM, OS kernel info")

    class Meta:
        verbose_name = "Scientific Experiment"
        verbose_name_plural = "Scientific Experiments"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.get_status_display()}]"


class ScientificDataset(TimeStampedModel):
    """Publication-ready, immutable dataset generated from validated experimental runs."""
    experiment = models.ForeignKey(ScientificExperiment, on_delete=models.CASCADE, related_name='datasets')
    dataset_name = models.CharField(max_length=255)
    semantic_version = models.CharField(max_length=20, default='1.0.0')
    description = models.TextField(blank=True)
    total_observations = models.PositiveIntegerField(default=0)
    total_outliers = models.PositiveIntegerField(default=0)
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    is_immutable = models.BooleanField(default=True)
    data_quality_score = models.FloatField(default=100.0, help_text="Data Quality Score (0-100)")
    confidence_index = models.FloatField(default=0.0, help_text="Statistical Confidence Index (0-100)")

    class Meta:
        verbose_name = "Scientific Dataset"
        verbose_name_plural = "Scientific Datasets"
        ordering = ['-created_at']
        unique_together = ('dataset_name', 'semantic_version')

    def __str__(self):
        return f"{self.dataset_name} v{self.semantic_version} (Score: {self.confidence_index:.1f}%)"


class DatasetObservation(TimeStampedModel):
    """Granular observation record representing a single measured benchmark repetition."""
    dataset = models.ForeignKey(ScientificDataset, on_delete=models.CASCADE, related_name='observations')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='observations')
    iteration_number = models.PositiveIntegerField()
    is_warmup = models.BooleanField(default=False)
    
    execution_time_ns = models.BigIntegerField(help_text="Execution latency in nanoseconds")
    execution_time_ms = models.FloatField(help_text="Execution latency in milliseconds")
    cpu_utilization_pct = models.FloatField(help_text="CPU percentage during execution")
    ram_rss_bytes = models.BigIntegerField(help_text="RAM Resident Set Size in bytes")
    ram_rss_mb = models.FloatField(help_text="RAM Resident Set Size in MB")
    energy_joules = models.FloatField(help_text="CPU Package Energy in Joules")
    co2_emissions_g = models.FloatField(help_text="Estimated carbon emissions in grams CO2eq")
    power_watts = models.FloatField(help_text="Average power consumption in Watts")
    
    is_outlier = models.BooleanField(default=False)
    outlier_score = models.FloatField(default=0.0, help_text="Z-score, IQR distance, or MAD metric")

    class Meta:
        verbose_name = "Dataset Observation"
        verbose_name_plural = "Dataset Observations"
        ordering = ['iteration_number']


class StatisticalSummary(TimeStampedModel):
    """Precomputed descriptive statistics for a specific library within a scientific dataset."""
    dataset = models.ForeignKey(ScientificDataset, on_delete=models.CASCADE, related_name='statistics')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='statistics')
    metric_name = models.CharField(max_length=50, help_text="e.g. execution_time_ms, energy_joules, ram_rss_mb")
    
    sample_size = models.PositiveIntegerField()
    mean = models.FloatField()
    median = models.FloatField()
    std_dev = models.FloatField()
    variance = models.FloatField()
    min_val = models.FloatField()
    max_val = models.FloatField()
    range_val = models.FloatField()
    iqr = models.FloatField()
    coefficient_of_variation = models.FloatField(help_text="CV (%) = (std_dev / mean) * 100")
    
    ci_95_lower = models.FloatField(help_text="95% Confidence Interval Lower Bound")
    ci_95_upper = models.FloatField(help_text="95% Confidence Interval Upper Bound")
    ci_99_lower = models.FloatField(help_text="99% Confidence Interval Lower Bound")
    ci_99_upper = models.FloatField(help_text="99% Confidence Interval Upper Bound")
    
    is_normally_distributed = models.BooleanField(default=True)
    normality_p_value = models.FloatField(default=1.0)

    class Meta:
        verbose_name = "Statistical Summary"
        verbose_name_plural = "Statistical Summaries"


class HypothesisTestResult(TimeStampedModel):
    """Formal inferential hypothesis test comparing two candidate libraries."""
    dataset = models.ForeignKey(ScientificDataset, on_delete=models.CASCADE, related_name='hypothesis_tests')
    baseline_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='baseline_tests')
    target_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='target_tests')
    metric_name = models.CharField(max_length=50)
    
    test_type = models.CharField(max_length=30, choices=HypothesisTestChoices.choices)
    test_statistic = models.FloatField()
    p_value = models.FloatField()
    alpha = models.FloatField(default=0.05)
    reject_null_hypothesis = models.BooleanField(default=False)
    
    effect_size_name = models.CharField(max_length=50, default="Cohen's d")
    effect_size_value = models.FloatField(default=0.0)
    effect_size_magnitude = models.CharField(max_length=30, default="Negligible")
    interpretation = models.TextField()

    class Meta:
        verbose_name = "Hypothesis Test Result"
        verbose_name_plural = "Hypothesis Test Results"


class ValidationReport(TimeStampedModel):
    """Data quality and experimental integrity validation audit report."""
    dataset = models.OneToOneField(ScientificDataset, on_delete=models.CASCADE, related_name='validation_report')
    is_valid = models.BooleanField(default=True)
    passed_rules_count = models.PositiveIntegerField(default=0)
    failed_rules_count = models.PositiveIntegerField(default=0)
    validation_details = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Validation Report"
        verbose_name_plural = "Validation Reports"
