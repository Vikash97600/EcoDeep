import time
import threading
import psutil

class ContinuousSamplerThread(threading.Thread):
    """Background thread polling process CPU utilization and RSS memory footprint."""

    def __init__(self, interval_sec=0.02):
        super().__init__(daemon=True)
        self.interval_sec = interval_sec
        self._stop_event = threading.Event()
        self.cpu_samples = []
        self.memory_samples_mb = []
        self.process = psutil.Process()

    def run(self):
        # Warmup psutil CPU percent calculation
        self.process.cpu_percent(interval=None)
        
        while not self._stop_event.is_set():
            try:
                cpu_pct = self.process.cpu_percent(interval=None)
                mem_rss_mb = self.process.memory_info().rss / (1024 * 1024)

                self.cpu_samples.append(cpu_pct)
                self.memory_samples_mb.append(mem_rss_mb)
            except Exception:
                pass
            time.sleep(self.interval_sec)

    def stop(self):
        self._stop_event.set()
        self.join(timeout=1.0)
