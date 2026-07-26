import os
import time
from apps.benchmark.plugins.energy.provider import BaseEnergyProvider

RAPL_SYSFS_PATH = "/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"

class IntelRaplProvider(BaseEnergyProvider):
    """Intel RAPL hardware counter provider for bare-metal Linux nodes."""

    def __init__(self):
        self._start_energy_uj = 0
        self._start_time = 0

    @property
    def name(self) -> str:
        return 'intel_rapl'

    def is_available(self) -> bool:
        return os.path.exists(RAPL_SYSFS_PATH) and os.access(RAPL_SYSFS_PATH, os.R_OK)

    def _read_uj(self) -> int:
        with open(RAPL_SYSFS_PATH, 'r') as f:
            return int(f.read().strip())

    def start(self) -> None:
        if self.is_available():
            self._start_energy_uj = self._read_uj()
            self._start_time = time.perf_counter()

    def stop(self) -> dict:
        if not self.is_available():
            return {'energy_joules': 0.0, 'co2_grams': 0.0, 'provider': self.name}

        stop_uj = self._read_uj()
        elapsed_sec = time.perf_counter() - self._start_time
        delta_uj = stop_uj - self._start_energy_uj

        energy_joules = round(delta_uj / 1e6, 4)
        energy_kwh = energy_joules / 3.6e6
        # India Grid Intensity default: 475 gCO2/kWh
        co2_grams = round(energy_kwh * 475.0, 4)

        return {
            'energy_joules': energy_joules,
            'co2_grams': co2_grams,
            'provider': self.name
        }
