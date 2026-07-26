from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, StatusChoices

class PluginCategoryChoices(models.TextChoices):
    BENCHMARK_RUNNER = 'BENCHMARK_RUNNER', 'Benchmark Runner Harness Plugin'
    MEASUREMENT_SENSOR = 'MEASUREMENT_SENSOR', 'Physical Measurement Sensor Plugin'
    ENERGY_PROVIDER = 'ENERGY_PROVIDER', 'Energy & Carbon Provider Plugin'
    GREEN_SCORE_STRATEGY = 'GREEN_SCORE_STRATEGY', 'Green Score Strategy Plugin'
    RECOMMENDATION_STRATEGY = 'RECOMMENDATION_STRATEGY', 'Recommendation Strategy Plugin'
    EXPORT_GENERATOR = 'EXPORT_GENERATOR', 'Data Exporter Plugin'


class PluginManifest(TimeStampedModel):
    """Database registry tracking discovered, installed, and active SDK plugins."""
    plugin_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    version = models.CharField(max_length=20, default='1.0.0')
    author = models.CharField(max_length=100, default='EcoDep Core Team')
    category = models.CharField(max_length=30, choices=PluginCategoryChoices.choices)
    description = models.TextField()
    entry_class = models.CharField(max_length=255, help_text="Python import path to entry plugin class")
    checksum_sha256 = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)
    is_system_plugin = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Plugin Manifest"
        verbose_name_plural = "Plugin Manifests"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} v{self.version} [{self.get_category_display()}] ({self.status})"


class PluginLog(TimeStampedModel):
    """Audit log tracking plugin execution traces, warnings, and error exceptions."""
    plugin = models.ForeignKey(PluginManifest, on_delete=models.CASCADE, related_name='logs')
    log_level = models.CharField(max_length=20, default='INFO')
    message = models.TextField()
    traceback = models.TextField(blank=True)

    class Meta:
        verbose_name = "Plugin Log"
        verbose_name_plural = "Plugin Logs"
        ordering = ['-created_at']


class PluginEvent(TimeStampedModel):
    """Event bus ledger tracking emitted platform events for subscriber plugins."""
    event_type = models.CharField(max_length=100)
    payload_json = models.TextField(default='{}')

    class Meta:
        verbose_name = "Plugin Event"
        verbose_name_plural = "Plugin Events"
        ordering = ['-created_at']
