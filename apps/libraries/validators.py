from django.core.exceptions import ValidationError


def validate_package_name(value):
    """Validates that package names contain valid PyPI/npm characters."""
    if not value.replace('-', '_').replace('.', '_').isalnum():
        raise ValidationError("Package name can only contain alphanumeric characters, hyphens, underscores, and dots.")

def validate_positive_metric(value):
    """Validates that download and star counts are non-negative."""
    if value < 0:
        raise ValidationError("Metric count cannot be negative.")
