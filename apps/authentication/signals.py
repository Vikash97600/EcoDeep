from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import Role, RoleChoices, UserProfile


@receiver(post_save, sender=User)
def create_default_user_profile(sender, instance, created, **kwargs):
    """Automatically creates a default UserProfile when a User is registered if not present."""
    if created and not hasattr(instance, 'profile'):
        default_role = Role.objects.filter(role_name=RoleChoices.DEVELOPER).first()
        UserProfile.objects.create(
            user=instance,
            role=default_role,
            status='ACTIVE'
        )
