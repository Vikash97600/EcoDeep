from apps.plugins.sdk.interfaces import EnergyProviderPlugin
from apps.plugins.sdk.manifest import PluginMetadata

class EnergyMeasurementPlugin(EnergyProviderPlugin):
    """Reference implementation of a physical CPU package energy & carbon plugin."""

    DEFAULT_TDP_WATTS = 45.0  # Core TDP baseline in Watts
    GRID_CARBON_INTENSITY = 0.475  # kg CO2 / kWh (Global Average)

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            plugin_id="ecodep.sensor.energy",
            name="Physical Energy & Carbon Sensor Plugin",
            version="1.0.0",
            author="EcoDep Core Team",
            category="ENERGY_PROVIDER",
            description="Measures physical package energy (Joules) and estimates carbon emissions (gCO2eq)",
            entry_class="apps.plugins.sample_plugins.energy_measurement_plugin.EnergyMeasurementPlugin"
        )

    def measure_energy_joules(self, duration_seconds: float) -> float:
        return round(self.DEFAULT_TDP_WATTS * duration_seconds, 4)

    def estimate_co2_grams(self, energy_joules: float) -> float:
        energy_kwh = energy_joules / 3.6e6
        return round(energy_kwh * self.GRID_CARBON_INTENSITY * 1000, 6)
