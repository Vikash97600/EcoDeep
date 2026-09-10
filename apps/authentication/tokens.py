from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """Generates unique security tokens for email activation verification."""
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + str(timestamp) +
            str(getattr(user, 'profile', None).email_verified if hasattr(user, 'profile') else False)
        )

account_activation_token = AccountActivationTokenGenerator()
