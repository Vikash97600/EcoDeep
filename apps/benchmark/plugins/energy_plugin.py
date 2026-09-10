from apps.benchmark.plugins import BaseMeasurementPlugin, MeasurementPluginRegistry
from apps.benchmark.plugins.energy.manager import EnergyManager


@MeasurementPluginRegistry.register
class EnergyMeasurementPlugin(BaseMeasurementPlugin):
    """Energy and carbon emissions measurement plugin for EcoDep."""

    def __init__(self):
        self.provider = None

    @property
    def name(self) -> str:
        return 'energy_plugin'

    def start(self) -> None:
        self.provider = EnergyManager.get_best_provider()
        if self.provider:
            self.provider.start()

    def stop(self) -> dict:
        if self.provider:
            return self.provider.stop()
        return {'energy_joules': 0.0, 'co2_grams': 0.0, 'provider': 'none'}
