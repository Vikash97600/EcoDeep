from apps.carbon.models import CarbonSavingsEstimate, RegionalGridCarbonFactor
from apps.carbon.services.carbon_service import CarbonService
from apps.libraries.models import Library


class CarbonSavingsService:
    """Calculates environmental equivalencies: trees planted, vehicle km avoided, and cost savings."""

    # Standard EPA / Environmental Conversion Constants
    KG_CO2_PER_TREE_YEAR = 21.77  # 1 mature urban tree absorbs ~21.77 kg CO2 / year
    G_CO2_PER_VEHICLE_KM = 120.0  # Average passenger car produces 120 g CO2 / km
    ELECTRICITY_COST_USD_PER_KWH = 0.14  # Commercial cloud rate $0.14 / kWh

    @staticmethod
    def calculate_savings(
        source_lib: Library,
        target_lib: Library,
        source_energy_joules: float,
        target_energy_joules: float,
        grid: RegionalGridCarbonFactor,
        requests_per_year: int = 10000000
    ) -> CarbonSavingsEstimate:
        """Calculates environmental savings and creates a CarbonSavingsEstimate."""
        CarbonService.calculate_emissions(source_energy_joules, grid)
        CarbonService.calculate_emissions(target_energy_joules, grid)

        delta_joules_per_req = max(0.0, source_energy_joules - target_energy_joules)
        delta_kwh_annual = (delta_joules_per_req * requests_per_year) / 3600000.0
        
        delta_carbon_g_annual = delta_kwh_annual * grid.carbon_intensity_g_per_kwh * grid.pue_factor
        delta_carbon_kg_annual = delta_carbon_g_annual / 1000.0

        pct_reduction = 0.0
        if source_energy_joules > 0:
            pct_reduction = round(((source_energy_joules - target_energy_joules) / source_energy_joules) * 100.0, 1)

        # Environmental Equivalencies
        trees_equiv = round(delta_carbon_kg_annual / CarbonSavingsService.KG_CO2_PER_TREE_YEAR, 2)
        car_km_avoided = round(delta_carbon_g_annual / CarbonSavingsService.G_CO2_PER_VEHICLE_KM, 1)
        cost_saved = round(delta_kwh_annual * CarbonSavingsService.ELECTRICITY_COST_USD_PER_KWH, 2)

        narrative = (
            f"Migrating from '{source_lib.library_name}' to '{target_lib.library_name}' in region '{grid.region_name}' "
            f"reduces annual emissions by {pct_reduction}% (-{delta_carbon_kg_annual:.1f} kg CO2e at {requests_per_year:,} requests/yr). "
            f"This environmental impact is equivalent to planting {trees_equiv:.1f} urban trees or avoiding {car_km_avoided:,.0f} km of vehicle driving."
        )

        estimate, _ = CarbonSavingsEstimate.objects.update_or_create(
            source_library=source_lib,
            target_library=target_lib,
            regional_grid=grid,
            defaults={
                'requests_per_year': requests_per_year,
                'energy_saved_kwh': round(delta_kwh_annual, 4),
                'carbon_saved_kg': round(delta_carbon_kg_annual, 2),
                'carbon_reduction_pct': max(0.0, pct_reduction),
                'trees_equivalent': trees_equiv,
                'vehicle_km_avoided': car_km_avoided,
                'cost_saved_usd': cost_saved,
                'explanation_narrative': narrative
            }
        )
        return estimate
