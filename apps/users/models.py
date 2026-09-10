from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import StatusChoices, TimeStampedModel

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Phone number must be entered in format: '+999999999'. Up to 15 digits allowed."
)

class RoleChoices(models.TextChoices):
    ADMIN = 'ADMIN', 'System Administrator'
    RESEARCHER = 'RESEARCHER', 'Academic Researcher'
    DEVELOPER = 'DEVELOPER', 'Software Developer'
    VISITOR = 'VISITOR', 'Guest Visitor'


class Role(TimeStampedModel):
    """Defines system roles and permission summaries."""
    role_name = models.CharField(max_length=50, choices=RoleChoices.choices, unique=True)
    description = models.TextField(blank=True, help_text="Detailed role responsibilities")
    permissions_summary = models.TextField(blank=True, help_text="Summary of system permissions")
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        ordering = ['role_name']

    def __str__(self):
        return self.get_role_name_display()


class UserProfile(TimeStampedModel):
    """Extends Django's built-in User model with application-specific metadata."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name='users')
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/avatars/', blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, help_text="e.g. Senior Software Architect")
    research_interest = models.CharField(max_length=255, blank=True, help_text="e.g. Green Computing, ML Efficiency")
    bio = models.TextField(blank=True, max_length=500)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ({self.role.role_name if self.role else 'No Role'})"
