from apps.benchmark.plugins import BaseMeasurementPlugin, MeasurementPluginRegistry
from apps.benchmark.services.sampling_manager import ContinuousSamplerThread
from apps.benchmark.services.statistics_service import StatisticalAnalysisService


@MeasurementPluginRegistry.register
class CpuMeasurementPlugin(BaseMeasurementPlugin):
    """Continuous CPU utilization measurement plugin."""

    def __init__(self):
        self.sampler = None

    @property
    def name(self) -> str:
        return 'cpu_plugin'

    def start(self) -> None:
        self.sampler = ContinuousSamplerThread(interval_sec=0.02)
        self.sampler.start()

    def stop(self) -> dict:
        if self.sampler:
            self.sampler.stop()
            cpu_samples = self.sampler.cpu_samples
            stats = StatisticalAnalysisService.calculate_statistics(cpu_samples)
            return {
                'average_cpu': stats.get('mean_ms', 0.0),
                'peak_cpu': stats.get('max_ms', 0.0),
                'raw_cpu_samples': cpu_samples
            }
        return {'average_cpu': 0.0, 'peak_cpu': 0.0}
