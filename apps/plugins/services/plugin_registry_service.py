from apps.plugins.models import PluginManifest, StatusChoices
from apps.plugins.services.plugin_validator_service import PluginValidatorService


class PluginRegistryService:
    """Registers, enables, disables, and queries SDK plugins in database manifest."""

    @staticmethod
    def register_plugin_class(plugin_cls, is_system_plugin=False):
        """Registers plugin class into database manifest."""
        is_valid, msg = PluginValidatorService.validate_plugin_class(plugin_cls)
        if not is_valid:
            raise ValueError(f"Plugin registration failed: {msg}")

        meta = plugin_cls.get_metadata()
        manifest, _created = PluginManifest.objects.update_or_create(
            plugin_id=meta.plugin_id,
            defaults={
                'name': meta.name,
                'version': meta.version,
                'author': meta.author,
                'category': meta.category,
                'description': meta.description,
                'entry_class': meta.entry_class,
                'is_system_plugin': is_system_plugin,
                'status': StatusChoices.ACTIVE
            }
        )
        return manifest

    @staticmethod
    def toggle_plugin_status(plugin_id: str, enable: bool):
        """Enables or disables an installed SDK plugin."""
        manifest = PluginManifest.objects.get(plugin_id=plugin_id)
        manifest.status = StatusChoices.ACTIVE if enable else StatusChoices.INACTIVE
        manifest.save()
        return manifest
