import importlib

from apps.plugins.models import PluginManifest, StatusChoices
from apps.plugins.services.plugin_validator_service import PluginValidatorService


class PluginLoaderService:
    """Dynamically loads and instantiates SDK plugins into active runtime memory."""

    @staticmethod
    def load_plugin_by_id(plugin_id: str):
        """Instantiates plugin class given its plugin_id if status is ACTIVE."""
        try:
            manifest = PluginManifest.objects.get(plugin_id=plugin_id, status=StatusChoices.ACTIVE)
        except PluginManifest.DoesNotExist:
            raise ValueError(f"Active plugin with ID '{plugin_id}' not found in registry.")

        module_name, class_name = manifest.entry_class.rsplit('.', 1)
        module = importlib.import_module(module_name)
        plugin_cls = getattr(module, class_name)

        is_valid, msg = PluginValidatorService.validate_plugin_class(plugin_cls)
        if not is_valid:
            raise ValueError(f"Plugin validation failed for '{plugin_id}': {msg}")

        instance = plugin_cls()
        instance.initialize()
        return instance
