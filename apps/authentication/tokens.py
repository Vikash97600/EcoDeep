from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Generates unique security tokens for email activation verification."""
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(getattr(user, 'profile', None).email_verified if hasattr(user, 'profile') else False)
        )

account_activation_token = AccountActivationTokenGenerator()
