from apps.benchmark.plugins.energy.provider import BaseEnergyProvider


class ScaphandreProvider(BaseEnergyProvider):
    """Scaphandre power metric exporter provider fallback."""

    @property
    def name(self) -> str:
        return 'scaphandre'

    def is_available(self) -> bool:
        return False  # Stub implementation for Scaphandre daemon fallback

    def start(self) -> None:
        pass

    def stop(self) -> dict:
        return {'energy_joules': 0.0, 'co2_grams': 0.0, 'provider': self.name}
