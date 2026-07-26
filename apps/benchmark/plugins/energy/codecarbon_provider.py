import logging
from apps.benchmark.plugins.energy.provider import BaseEnergyProvider

logger = logging.getLogger(__name__)

class CodeCarbonProvider(BaseEnergyProvider):
    """CodeCarbon telemetry provider with offline fallback."""

    def __init__(self):
        self._tracker = None

    @property
    def name(self) -> str:
        return 'codecarbon'

    def is_available(self) -> bool:
        try:
            import codecarbon
            return True
        except ImportError:
            return False

    def start(self) -> None:
        if self.is_available():
            try:
                from codecarbon import OfflineEmissionsTracker
                self._tracker = OfflineEmissionsTracker(country_iso_code="IND", log_level="error")
                self._tracker.start()
            except Exception as e:
                logger.warning(f"CodeCarbon start failed: {str(e)}")

    def stop(self) -> dict:
        energy_joules = 0.0
        co2_grams = 0.0

        if self._tracker:
            try:
                emissions_kg = self._tracker.stop()
                if emissions_kg is not None:
                    co2_grams = round(emissions_kg * 1000, 4)
                
                if hasattr(self._tracker, '_total_energy'):
                    energy_kwh = self._tracker._total_energy.kwh
                    energy_joules = round(energy_kwh * 3.6e6, 4)
            except Exception as e:
                logger.warning(f"CodeCarbon stop failed: {str(e)}")

        return {
            'energy_joules': energy_joules,
            'co2_grams': co2_grams,
            'provider': self.name
        }
