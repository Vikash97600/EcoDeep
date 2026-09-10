from abc import ABC, abstractmethod


class BaseEnergyProvider(ABC):
    """Abstract Base Class for hardware and software energy telemetry providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns unique provider string identifier."""

    @abstractmethod
    def is_available(self) -> bool:
        """Verifies hardware counter access or package availability."""

    @abstractmethod
    def start(self) -> None:
        """Hooks immediately prior to workload execution."""

    @abstractmethod
    def stop(self) -> dict:
        """Hooks immediately after workload execution. Returns Joules and CO2 dict."""
