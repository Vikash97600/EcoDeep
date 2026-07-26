import tracemalloc
import psutil
from apps.benchmark.plugins import BaseMeasurementPlugin, MeasurementPluginRegistry

@MeasurementPluginRegistry.register
class MemoryMeasurementPlugin(BaseMeasurementPlugin):
    """Process RSS and tracemalloc heap allocation measurement plugin."""

    def __init__(self):
        self.process = psutil.Process()

    @property
    def name(self) -> str:
        return 'memory_plugin'

    def start(self) -> None:
        tracemalloc.start()

    def stop(self) -> dict:
        current_bytes, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        rss_mb = round(self.process.memory_info().rss / (1024 * 1024), 2)
        peak_heap_mb = round(peak_bytes / (1024 * 1024), 2)

        return {
            'peak_memory': peak_heap_mb,
            'average_memory': rss_mb,
            'rss_memory_mb': rss_mb
        }
