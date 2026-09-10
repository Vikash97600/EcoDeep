import psutil


class ResourceMonitorService:
    """Resource-aware scheduling guard checking host CPU and RAM load thresholds (< 85%)."""

    MAX_CPU_THRESHOLD_PCT = 85.0
    MAX_RAM_THRESHOLD_PCT = 85.0

    @staticmethod
    def is_host_resource_available():
        """Returns True if host CPU and RAM utilization are below 85% safety limits."""
        cpu_pct = psutil.cpu_percent(interval=0.1)
        ram_pct = psutil.virtual_memory().percent

        is_safe = (cpu_pct < ResourceMonitorService.MAX_CPU_THRESHOLD_PCT) and (ram_pct < ResourceMonitorService.MAX_RAM_THRESHOLD_PCT)
        return is_safe, cpu_pct, ram_pct
