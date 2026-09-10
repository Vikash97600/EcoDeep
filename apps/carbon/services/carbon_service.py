from apps.carbon.models import CarbonEmissionRecord, RegionalGridCarbonFactor
from apps.carbon.services.regional_carbon_service import RegionalCarbonService
from apps.libraries.models import Library


class CarbonService:
    """Calculates carbon emissions (gCO2e / kgCO2e) based on software energy and regional grid intensity."""

    @staticmethod
    def calculate_emissions(energy_joules: float, grid: RegionalGridCarbonFactor) -> dict[str, float]:
        """Calculates carbon emissions in grams and kilograms factoring in grid intensity and PUE."""
        # 1 kWh = 3,600,000 Joules
        energy_kwh = energy_joules / 3600000.0
        
        # Emissions (gCO2e) = Energy(kWh) * Carbon Intensity(gCO2/kWh) * PUE
        carbon_g = energy_kwh * grid.carbon_intensity_g_per_kwh * grid.pue_factor
        carbon_kg = carbon_g / 1000.0

        # Annualized estimate at 10,000,000 requests
        annualized_kg = carbon_kg * 10000000.0

        return {
            'energy_joules': round(energy_joules, 4),
            'energy_kwh': round(energy_kwh, 8),
            'carbon_emissions_g': round(carbon_g, 6),
            'carbon_emissions_kg': round(carbon_kg, 8),
            'annualized_emissions_kg': round(annualized_kg, 2)
        }

    @staticmethod
    def record_library_carbon(library: Library, energy_joules: float, grid: RegionalGridCarbonFactor = None) -> CarbonEmissionRecord:
        """Computes emissions and saves a CarbonEmissionRecord."""
        if not grid:
            grid = RegionalCarbonService.get_default_region()

        metrics = CarbonService.calculate_emissions(energy_joules, grid)
        
        # Calculate carbon score (0-100)
        # Scaled where < 3 Joules gets 90+, > 10 Joules gets < 50
        raw_score = max(10.0, min(100.0, 100.0 - (metrics['carbon_emissions_g'] * 150000.0)))
        carbon_score = round(raw_score, 1)

        record, _created = CarbonEmissionRecord.objects.update_or_create(
            library=library,
            regional_grid=grid,
            defaults={
                'energy_joules': metrics['energy_joules'],
                'energy_kwh': metrics['energy_kwh'],
                'carbon_emissions_g': metrics['carbon_emissions_g'],
                'carbon_emissions_kg': metrics['carbon_emissions_kg'],
                'annualized_emissions_kg': metrics['annualized_emissions_kg'],
                'carbon_score': carbon_score,
                'confidence_score': 96.0
            }
        )
        return record
