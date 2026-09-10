from apps.carbon.models import CarbonForecast, RegionalGridCarbonFactor
from apps.carbon.services.carbon_service import CarbonService
from apps.carbon.services.regional_carbon_service import RegionalCarbonService
from apps.libraries.models import Library


class CarbonForecastService:
    """Projects multi-month software carbon emissions under growing traffic volumes."""

    @staticmethod
    def generate_12_month_forecast(library: Library, grid: RegionalGridCarbonFactor = None, base_monthly_requests: int = 1000000) -> CarbonForecast:
        """Projects monthly carbon footprint with 5% month-over-month traffic growth."""
        if not grid:
            grid = RegionalCarbonService.get_default_region()

        is_fast = 'fast' in library.library_name.lower() or 'ujson' in library.library_name.lower()
        energy_j = 2.15 if is_fast else 5.80
        per_req_metrics = CarbonService.calculate_emissions(energy_j, grid)

        monthly_projections = []
        growth_rate = 1.05  # 5% growth per month
        current_reqs = base_monthly_requests

        for m in range(1, 13):
            month_kg = (per_req_metrics['carbon_emissions_kg'] * current_reqs)
            monthly_projections.append({
                'month': m,
                'requests': int(current_reqs),
                'carbon_kg': round(month_kg, 3)
            })
            current_reqs *= growth_rate

        forecast, _ = CarbonForecast.objects.update_or_create(
            library=library,
            regional_grid=grid,
            defaults={
                'forecast_horizon_months': 12,
                'projected_monthly_emissions_kg': monthly_projections,
                'trend_slope': 0.05,
                'confidence_interval': 95.0
            }
        )
        return forecast
