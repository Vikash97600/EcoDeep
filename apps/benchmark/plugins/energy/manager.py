from apps.benchmark.plugins.energy.rapl_provider import IntelRaplProvider
from apps.benchmark.plugins.energy.codecarbon_provider import CodeCarbonProvider
from apps.benchmark.plugins.energy.scaphandre_provider import ScaphandreProvider

class EnergyManager:
    """Selects the highest accuracy available energy telemetry provider."""

    @staticmethod
    def get_best_provider():
        providers = [
            IntelRaplProvider(),
            CodeCarbonProvider(),
            ScaphandreProvider()
        ]

        for provider in providers:
            if provider.is_available():
                return provider

        # Fallback provider
        return CodeCarbonProvider()
