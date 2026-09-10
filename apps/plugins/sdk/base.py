from abc import ABC, abstractmethod

from apps.plugins.sdk.manifest import PluginMetadata


class BasePlugin(ABC):
    """Abstract base class that all EcoDep SDK plugins must inherit from."""

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> PluginMetadata:
        """Returns the plugin manifest metadata contract."""

    def initialize(self) -> bool:
        """Lifecycle hook called when plugin is loaded into runtime memory."""
        return True

    def shutdown(self) -> None:
        """Lifecycle hook called when plugin is unloaded or shut down."""
