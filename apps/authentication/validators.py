import re

from django.core.exceptions import ValidationError


class PasswordStrengthValidator:
    """Validates that passwords meet minimum complexity requirements (length, case, numbers, special characters)."""
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(f"Password must be at least {self.min_length} characters long.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter (A-Z).")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter (a-z).")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one numeric digit (0-9).")
        if not re.search(r'[@$!%*?&#^()_+\-=\[\]{};:\'",.<>/\\]', password):
            raise ValidationError("Password must contain at least one special character.")

    def get_help_text(self):
        return "Your password must be at least 8 characters long and contain uppercase, lowercase, numeric, and special characters."
