import time
from apps.benchmark.plugins import BaseMeasurementPlugin, MeasurementPluginRegistry
from apps.benchmark.services.statistics_service import StatisticalAnalysisService

@MeasurementPluginRegistry.register
class ExecutionTimePlugin(BaseMeasurementPlugin):
    """High-resolution nanosecond timer measurement plugin for EcoDep."""

    def __init__(self):
        self._start_time_ns = 0
        self._samples_ns = []

    @property
    def name(self) -> str:
        return 'execution_time_plugin'

    def start(self) -> None:
        """Invoked prior to workload loop iteration."""
        self._samples_ns = []
        self._start_time_ns = time.perf_counter_ns()

    def record_sample(self, start_ns, stop_ns):
        """Records an individual iteration nanosecond delta sample."""
        delta_ns = stop_ns - start_ns
        self._samples_ns.append(delta_ns)

    def stop(self) -> dict:
        """Invoked upon workload loop completion. Computes statistics."""
        total_delta_ns = time.perf_counter_ns() - self._start_time_ns
        stats = StatisticalAnalysisService.calculate_statistics(self._samples_ns)
        stats['total_elapsed_ms'] = round(total_delta_ns / 1e6, 4)
        return stats
