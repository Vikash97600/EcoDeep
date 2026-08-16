from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel, StatusChoices
from apps.libraries.models import Category, LibraryVersion, ProgrammingLanguage

class BenchmarkStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending Execution'
    RUNNING = 'RUNNING', 'Running Benchmarks'
    COMPLETED = 'COMPLETED', 'Successfully Completed'
    FAILED = 'FAILED', 'Execution Failed'
    CANCELLED = 'CANCELLED', 'Cancelled by Admin'


class DatasetTypeChoices(models.TextChoices):
    JSON = 'JSON', 'JSON Document Payload'
    CSV = 'CSV', 'Comma Separated Values'
    XML = 'XML', 'Extensible Markup Language'
    TXT = 'TXT', 'Plain Unstructured Text'
    IMAGE = 'IMAGE', 'Raster Image (JPEG/PNG)'


class BenchmarkDataset(TimeStampedModel):
    """Standardized input data payloads used across benchmarks."""
    dataset_name = models.CharField(max_length=150, unique=True)
    dataset_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='datasets')
    dataset_type = models.CharField(max_length=20, choices=DatasetTypeChoices.choices, default=DatasetTypeChoices.JSON)
    dataset_size_bytes = models.BigIntegerField(default=0, help_text="File size in bytes")
    checksum_sha256 = models.CharField(max_length=64, blank=True, help_text="SHA256 integrity hash")
    file_path = models.FileField(upload_to='benchmarks/datasets/', blank=True, null=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, blank=True)

    class Meta:
        verbose_name = "Benchmark Dataset"
        verbose_name_plural = "Benchmark Datasets"
        ordering = ['dataset_name']

    def __str__(self):
        return f"{self.dataset_name} ({self.dataset_type} - {self.dataset_size_bytes / (1024*1024):.2f} MB)"


class DatasetVersion(TimeStampedModel):
    """Tracks version releases of a dataset file."""
    dataset = models.ForeignKey(BenchmarkDataset, on_delete=models.CASCADE, related_name='versions')
    version_number = models.CharField(max_length=20, default='1.0.0')
    checksum_sha256 = models.CharField(max_length=64)
    file_path = models.FileField(upload_to='benchmarks/datasets/versions/')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Dataset Version"
        verbose_name_plural = "Dataset Versions"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dataset.dataset_name} v{self.version_number}"


class BenchmarkTask(TimeStampedModel):
    """Standardized computational workload tasks."""
    task_name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tasks')
    dataset = models.ForeignKey(BenchmarkDataset, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    description = models.TextField(blank=True)
    expected_output = models.CharField(max_length=255, default='dict / sha256', blank=True, help_text="Expected return type or output checksum")
    iterations = models.IntegerField(default=50, validators=[MinValueValidator(1)])
    warmup_runs = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    timeout_seconds = models.IntegerField(default=30, validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE, blank=True)

    class Meta:
        verbose_name = "Benchmark Task"
        verbose_name_plural = "Benchmark Tasks"
        ordering = ['task_name']

    def __str__(self):
        return self.task_name


class BenchmarkProfile(TimeStampedModel):
    """Saved reusable experiment profile configuration presets."""
    profile_name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    iterations = models.IntegerField(default=50)
    warmup_runs = models.IntegerField(default=5)
    timeout_seconds = models.IntegerField(default=30)
    random_seed = models.IntegerField(default=42)

    class Meta:
        verbose_name = "Benchmark Profile"
        verbose_name_plural = "Benchmark Profiles"
        ordering = ['profile_name']

    def __str__(self):
        return self.profile_name


class BenchmarkSession(TimeStampedModel):
    """Tracks host environment state during a benchmark execution run."""
    session_name = models.CharField(max_length=150, default='Standard Benchmark Session')
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
        return f"{self.session_name} (#{self.id}) - {self.status}"


class BenchmarkJob(TimeStampedModel):
    """Represents an individual executable job unit within a session queue."""
    session = models.ForeignKey(BenchmarkSession, on_delete=models.CASCADE, related_name='jobs')
    library_version = models.ForeignKey(LibraryVersion, on_delete=models.CASCADE, related_name='jobs')
    task = models.ForeignKey(BenchmarkTask, on_delete=models.CASCADE, related_name='jobs')
    status = models.CharField(max_length=20, choices=BenchmarkStatusChoices.choices, default=BenchmarkStatusChoices.PENDING)
    priority = models.IntegerField(default=3, help_text="1=Background, 2=Low, 3=Normal, 4=High, 5=Critical")
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    error_log = models.TextField(blank=True)

    class Meta:
        verbose_name = "Benchmark Job"
        verbose_name_plural = "Benchmark Jobs"
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f"Job #{self.id} [{self.library_version}] - {self.status} (Priority: {self.priority})"


class WorkerNode(TimeStampedModel):
    """Registered worker node executing benchmark harness tasks."""
    hostname = models.CharField(max_length=150, unique=True)
    ip_address = models.GenericIPAddressField(default='127.0.0.1')
    cpu_cores = models.IntegerField(default=8)
    ram_mb = models.IntegerField(default=16384)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    current_load_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    last_heartbeat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Worker Node"
        verbose_name_plural = "Worker Nodes"
        ordering = ['hostname']

    def __str__(self):
        return f"Worker Node: {self.hostname} ({self.status} - Load: {self.current_load_pct}%)"


class WorkerHeartbeat(TimeStampedModel):
    """Continuous heartbeat telemetry logging worker node CPU and RAM load."""
    worker = models.ForeignKey(WorkerNode, on_delete=models.CASCADE, related_name='heartbeats')
    cpu_percent = models.DecimalField(max_digits=5, decimal_places=2)
    memory_percent = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = "Worker Heartbeat"
        verbose_name_plural = "Worker Heartbeats"
        ordering = ['-created_at']


class JobRetryLog(TimeStampedModel):
    """Audit log tracking job failure exceptions, attempt numbers, and backoff delays."""
    job = models.ForeignKey(BenchmarkJob, on_delete=models.CASCADE, related_name='retry_logs')
    attempt_number = models.IntegerField()
    backoff_delay_seconds = models.DecimalField(max_digits=8, decimal_places=2)
    exception_trace = models.TextField()

    class Meta:
        verbose_name = "Job Retry Log"
        verbose_name_plural = "Job Retry Logs"
        ordering = ['-created_at']


class BenchmarkResult(TimeStampedModel):
    """Raw and aggregated physical telemetry collected during benchmark runs."""
    session = models.ForeignKey(BenchmarkSession, on_delete=models.CASCADE, related_name='results')
    library_version = models.ForeignKey(LibraryVersion, on_delete=models.CASCADE, related_name='benchmark_results')
    task = models.ForeignKey(BenchmarkTask, on_delete=models.CASCADE, related_name='results')
    dataset = models.ForeignKey(BenchmarkDataset, on_delete=models.CASCADE, related_name='results')
    
    execution_time = models.DecimalField(max_digits=12, decimal_places=4, default=0.0, help_text="Total execution time in milliseconds")
    average_execution_time = models.DecimalField(max_digits=12, decimal_places=4, default=0.0, help_text="Mean execution time per iteration (ms)")
    peak_memory = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Peak memory usage in MB")
    average_memory = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, help_text="Average memory usage in MB")
    cpu_usage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Percentage CPU utilization")
    average_cpu = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Mean CPU utilization %")
    energy = models.DecimalField(max_digits=12, decimal_places=4, default=0.0, help_text="Total CPU Package Energy in Joules")
    co2 = models.DecimalField(max_digits=10, decimal_places=4, default=0.0, help_text="Estimated CO2 emissions in grams")
    green_score = models.DecimalField(max_digits=7, decimal_places=4, default=0.0, help_text="Normalized Energy Score (NES)")
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
        return f"{self.library_version} | Task: {self.task.task_name} | Status: Recorded"


class RawExecutionSample(TimeStampedModel):
    """Persists raw nanosecond iteration samples for scientific auditing."""
    result = models.ForeignKey(BenchmarkResult, on_delete=models.CASCADE, related_name='raw_samples')
    iteration_number = models.IntegerField()
    elapsed_nanoseconds = models.BigIntegerField(help_text="Raw delta duration in nanoseconds")
    is_outlier = models.BooleanField(default=False, help_text="Flagged as outlier by IQR filter")

    class Meta:
        verbose_name = "Raw Execution Sample"
        verbose_name_plural = "Raw Execution Samples"
        ordering = ['iteration_number']

    def __str__(self):
        return f"Sample #{self.iteration_number} ({self.elapsed_nanoseconds / 1e6:.4f} ms)"


class RawCpuSample(TimeStampedModel):
    """Persists continuous CPU utilization telemetry samples."""
    result = models.ForeignKey(BenchmarkResult, on_delete=models.CASCADE, related_name='cpu_samples')
    sample_index = models.IntegerField()
    cpu_percent = models.DecimalField(max_digits=5, decimal_places=2)
    is_outlier = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Raw CPU Sample"
        verbose_name_plural = "Raw CPU Samples"
        ordering = ['sample_index']


class RawMemorySample(TimeStampedModel):
    """Persists continuous Resident Set Size (RSS) RAM telemetry samples."""
    result = models.ForeignKey(BenchmarkResult, on_delete=models.CASCADE, related_name='memory_samples')
    sample_index = models.IntegerField()
    rss_mb = models.DecimalField(max_digits=10, decimal_places=2)
    is_outlier = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Raw Memory Sample"
        verbose_name_plural = "Raw Memory Samples"
        ordering = ['sample_index']


class RawEnergySample(TimeStampedModel):
    """Persists continuous power and energy telemetry samples."""
    result = models.ForeignKey(BenchmarkResult, on_delete=models.CASCADE, related_name='energy_samples')
    sample_index = models.IntegerField()
    power_watts = models.DecimalField(max_digits=10, decimal_places=4)
    energy_joules = models.DecimalField(max_digits=12, decimal_places=4)
    is_outlier = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Raw Energy Sample"
        verbose_name_plural = "Raw Energy Samples"
        ordering = ['sample_index']
