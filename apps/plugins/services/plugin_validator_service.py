import hashlib
import inspect
from apps.plugins.sdk.base import BasePlugin

class PluginValidatorService:
    """Validates plugin manifest schema, class inheritance, and SHA256 checksum integrity."""

    @staticmethod
    def validate_plugin_class(plugin_cls) -> tuple[bool, str]:
        """Ensures plugin class inherits from BasePlugin and implements required abstract methods."""
        if not inspect.isclass(plugin_cls):
            return False, "Target plugin entry point is not a class."
        
        if not issubclass(plugin_cls, BasePlugin):
            return False, f"Plugin class {plugin_cls.__name__} does not inherit from BasePlugin."

        try:
            metadata = plugin_cls.get_metadata()
            if not metadata.plugin_id or not metadata.name or not metadata.entry_class:
                return False, "Plugin manifest metadata missing required fields."
        except Exception as e:
            return False, f"Failed to retrieve plugin metadata: {str(e)}"

        return True, "Plugin validated successfully."

    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        """Calculates SHA256 checksum for plugin bundle integrity verification."""
        return hashlib.sha256(file_content).hexdigest()
