from django.contrib.auth.models import User
from django.db import models

from apps.core.models import TimeStampedModel


class APIKey(TimeStampedModel):
    """API authentication key for external clients (IDE extensions, CI/CD pipelines)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    key_name = models.CharField(max_length=100)
    key_value = models.CharField(max_length=64, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.key_name} ({self.user.username})"


class APIUsageLog(TimeStampedModel):
    """Audit log tracking API request traffic, endpoints, and status codes."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    endpoint = models.CharField(max_length=255)
    http_method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "API Usage Log"
        verbose_name_plural = "API Usage Logs"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.http_method} {self.endpoint} [{self.status_code}]"
