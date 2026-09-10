from abc import abstractmethod
from typing import Any

from apps.plugins.sdk.base import BasePlugin


class MeasurementPlugin(BasePlugin):
    """Interface for physical telemetry measurement sensors (latency, CPU, RAM, RAPL)."""

    @abstractmethod
    def start_measurement(self) -> None:
        """Starts physical sensor sampling."""

    @abstractmethod
    def stop_measurement(self) -> dict[str, Any]:
        """Stops physical sampling and returns sensor telemetry metrics dictionary."""


class BenchmarkPlugin(BasePlugin):
    """Interface for language benchmark workload execution harnesses."""

    @abstractmethod
    def execute_workload(self, task_config: dict[str, Any]) -> dict[str, Any]:
        """Executes targeted benchmark workload task."""


class EnergyProviderPlugin(BasePlugin):
    """Interface for physical CPU package energy & carbon emissions calculators."""

    @abstractmethod
    def measure_energy_joules(self, duration_seconds: float) -> float:
        """Measures CPU package energy consumption in Joules."""

    @abstractmethod
    def estimate_co2_grams(self, energy_joules: float) -> float:
        """Estimates carbon emissions footprint in grams of CO2 equivalent."""


class ExportPlugin(BasePlugin):
    """Interface for custom research data exporters."""

    @abstractmethod
    def export_data(self, dataset: list[dict[str, Any]]) -> bytes:
        """Serializes research telemetry dataset into downloadable binary payload."""
