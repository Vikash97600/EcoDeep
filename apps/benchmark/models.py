from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel, StatusChoices
from apps.libraries.models import Category, LibraryVersion

class BenchmarkStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending Execution'
    RUNNING = 'RUNNING', 'Running Benchmarks'
    COMPLETED = 'COMPLETED', 'Successfully Completed'
    FAILED = 'FAILED', 'Execution Failed'


class BenchmarkDataset(TimeStampedModel):
    """Standardized input data payloads used across benchmarks."""
    dataset_name = models.CharField(max_length=150, unique=True)
    dataset_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='datasets')
    dataset_size_bytes = models.BigIntegerField(help_text="File size in bytes")
    file_path = models.FileField(upload_to='benchmarks/datasets/')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Benchmark Dataset"
        verbose_name_plural = "Benchmark Datasets"
        ordering = ['dataset_name']

    def __str__(self):
        return f"{self.dataset_name} ({self.dataset_size_bytes / (1024*1024):.2f} MB)"


class BenchmarkTask(TimeStampedModel):
    """Standardized computational workload tasks."""
    task_name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tasks')
    dataset = models.ForeignKey(BenchmarkDataset, on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()
    expected_output = models.CharField(max_length=255, help_text="Expected return type or output checksum")
    iterations = models.IntegerField(default=50, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Benchmark Task"
        verbose_name_plural = "Benchmark Tasks"
        ordering = ['task_name']

    def __str__(self):
        return self.task_name


class BenchmarkSession(TimeStampedModel):
    """Tracks host environment state during a benchmark execution run."""
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    machine_name = models.CharField(max_length=100, default='BenchTestbed-01')
    operating_system = models.CharField(max_length=100, default='Ubuntu 22.04 LTS')
    cpu = models.CharField(max_length=150, default='Intel Core i7-12700K')
    ram = models.CharField(max_length=50, default='32 GB DDR4')
    python_version = models.CharField(max_length=50, default='Python 3.11.4')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=BenchmarkStatusChoices.choices, default=BenchmarkStatusChoices.PENDING)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Benchmark Session"
        verbose_name_plural = "Benchmark Sessions"
        ordering = ['-start_time']

    def __str__(self):
        return f"Session #{self.id} - {self.machine_name} ({self.status})"


class BenchmarkResult(TimeStampedModel):
    """Raw and aggregated physical telemetry collected during benchmark runs."""
    session = models.ForeignKey(BenchmarkSession, on_delete=models.CASCADE, related_name='results')
    library_version = models.ForeignKey(LibraryVersion, on_delete=models.CASCADE, related_name='benchmark_results')
    task = models.ForeignKey(BenchmarkTask, on_delete=models.CASCADE, related_name='results')
    dataset = models.ForeignKey(BenchmarkDataset, on_delete=models.CASCADE, related_name='results')
    
    execution_time = models.DecimalField(max_digits=12, decimal_places=4, help_text="Total execution time in milliseconds")
    average_execution_time = models.DecimalField(max_digits=12, decimal_places=4, help_text="Mean execution time per iteration (ms)")
    peak_memory = models.DecimalField(max_digits=10, decimal_places=2, help_text="Peak memory usage in MB")
    average_memory = models.DecimalField(max_digits=10, decimal_places=2, help_text="Average memory usage in MB")
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage CPU utilization")
    average_cpu = models.DecimalField(max_digits=5, decimal_places=2, help_text="Mean CPU utilization %")
    energy = models.DecimalField(max_digits=12, decimal_places=4, help_text="Total CPU Package Energy in Joules")
    co2 = models.DecimalField(max_digits=10, decimal_places=4, help_text="Estimated CO2 emissions in grams")
    green_score = models.DecimalField(max_digits=6, decimal_places=4, help_text="Normalized Energy Score (NES)")
    iterations = models.IntegerField(default=50)
    remarks = models.TextField(blank=True)

    class Meta:
        verbose_name = "Benchmark Result"
        verbose_name_plural = "Benchmark Results"
        ordering = ['green_score', 'execution_time']
        indexes = [
            models.Index(fields=['library_version', 'task']),
            models.Index(fields=['green_score']),
        ]

    def __str__(self):
        return f"{self.library_version} | Task: {self.task.task_name} | NES: {self.green_score}"
