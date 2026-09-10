from django.contrib.auth.models import User
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model providing self-updating creation and modification timestamps."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class StatusChoices(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    ARCHIVED = 'ARCHIVED', 'Archived'


class AuditLog(models.Model):
    """Records administrative and security events for system auditing."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100, help_text="e.g. USER_LOGIN, BENCHMARK_EXECUTE")
    module = models.CharField(max_length=50, help_text="e.g. authentication, benchmark")
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.action} by {self.user.username if self.user else 'System'}"


class SystemSettings(models.Model):
    """Stores system-wide dynamic configuration key-value parameters."""
    setting_name = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        ordering = ['setting_name']

    def __str__(self):
        return f"{self.setting_name} = {self.setting_value}"
