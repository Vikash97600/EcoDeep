import platform
import sys
import psutil

class EnvironmentService:
    """Queries host testbed hardware specs, OS kernel, and Python runtime for benchmark validation."""

    @staticmethod
    def get_host_environment():
        return {
            'machine_name': platform.node() or 'BenchTestbed-01',
            'operating_system': f"{platform.system()} {platform.release()} ({platform.machine()})",
            'cpu': f"{platform.processor() or 'Intel/AMD CPU'} ({psutil.cpu_count(logical=False)} Cores / {psutil.cpu_count(logical=True)} Threads)",
            'ram': f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB DDR4",
            'python_version': f"Python {sys.version.split()[0]} ({platform.architecture()[0]})",
        }

    @staticmethod
    def validate_environment():
        """Checks host CPU utilization and memory availability prior to starting benchmark sessions."""
        cpu_load = psutil.cpu_percent(interval=0.5)
        mem_avail_gb = round(psutil.virtual_memory().available / (1024**3), 2)
        
        is_valid = cpu_load < 20.0 and mem_avail_gb > 1.0
        details = f"Host CPU Utilization: {cpu_load}%, Available RAM: {mem_avail_gb} GB"
        
        return is_valid, details
