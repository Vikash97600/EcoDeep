from abc import ABC, abstractmethod


class BaseMeasurementPlugin(ABC):
    """Abstract Base Class for all physical measurement plugins (Time, CPU, RAM, RAPL Energy)."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Returns plugin name identifier."""

    @abstractmethod
    def start(self) -> None:
        """Hook called immediately prior to benchmark workload loop execution."""

    @abstractmethod
    def stop(self) -> dict:
        """Hook called immediately following benchmark workload loop completion. Returns metric dict."""


class MeasurementPluginRegistry:
    """Central registry tracking active measurement plugins."""
    _plugins = {}

    @classmethod
    def register(cls, plugin_cls):
        plugin_instance = plugin_cls()
        cls._plugins[plugin_instance.name] = plugin_instance
        return plugin_cls

    @classmethod
    def get_registered_plugins(cls):
        return cls._plugins
