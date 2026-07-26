from abc import abstractmethod
from typing import Dict, Any, List
from apps.plugins.sdk.base import BasePlugin

class MeasurementPlugin(BasePlugin):
    """Interface for physical telemetry measurement sensors (latency, CPU, RAM, RAPL)."""

    @abstractmethod
    def start_measurement(self) -> None:
        """Starts physical sensor sampling."""
        pass

    @abstractmethod
    def stop_measurement(self) -> Dict[str, Any]:
        """Stops physical sampling and returns sensor telemetry metrics dictionary."""
        pass


class BenchmarkPlugin(BasePlugin):
    """Interface for language benchmark workload execution harnesses."""

    @abstractmethod
    def execute_workload(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """Executes targeted benchmark workload task."""
        pass


class EnergyProviderPlugin(BasePlugin):
    """Interface for physical CPU package energy & carbon emissions calculators."""

    @abstractmethod
    def measure_energy_joules(self, duration_seconds: float) -> float:
        """Measures CPU package energy consumption in Joules."""
        pass

    @abstractmethod
    def estimate_co2_grams(self, energy_joules: float) -> float:
        """Estimates carbon emissions footprint in grams of CO2 equivalent."""
        pass


class ExportPlugin(BasePlugin):
    """Interface for custom research data exporters."""

    @abstractmethod
    def export_data(self, dataset: List[Dict[str, Any]]) -> bytes:
        """Serializes research telemetry dataset into downloadable binary payload."""
        pass
