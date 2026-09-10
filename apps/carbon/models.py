from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import StatusChoices, TimeStampedModel
from apps.libraries.models import Library


class CloudProviderChoices(models.TextChoices):
    AWS = 'AWS', 'Amazon Web Services'
    GCP = 'GCP', 'Google Cloud Platform'
    AZURE = 'AZURE', 'Microsoft Azure'
    NATIONAL_GRID = 'NATIONAL_GRID', 'National Public Electrical Grid'
    ON_PREMISE = 'ON_PREMISE', 'On-Premise Private Datacenter'


class RegionalGridCarbonFactor(TimeStampedModel):
    """Stores regional electrical grid carbon intensity factors (gCO2/kWh) and PUE."""
    region_code = models.CharField(max_length=50, unique=True, help_text="e.g. us-east-1, eu-west-1, in-west-1")
    region_name = models.CharField(max_length=150)
    provider = models.CharField(max_length=30, choices=CloudProviderChoices.choices, default=CloudProviderChoices.AWS)
    country = models.CharField(max_length=100)
    
    # Emission Factors
    carbon_intensity_g_per_kwh = models.FloatField(help_text="Grid carbon intensity in gCO2e per kWh (e.g. 385.0)")
    pue_factor = models.FloatField(default=1.15, validators=[MinValueValidator(1.0), MaxValueValidator(3.0)], help_text="Power Usage Effectiveness (PUE)")
    renewable_share_pct = models.FloatField(default=25.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])
    
    is_default = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.ACTIVE)

    class Meta:
        verbose_name = "Regional Grid Carbon Factor"
        verbose_name_plural = "Regional Grid Carbon Factors"
        ordering = ['region_code']

    def __str__(self):
        return f"{self.region_name} ({self.region_code}) [{self.carbon_intensity_g_per_kwh} gCO2/kWh]"


class CarbonEmissionRecord(TimeStampedModel):
    """Stores calculated carbon emissions for a library under a specific regional grid profile."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='carbon_records')
    regional_grid = models.ForeignKey(RegionalGridCarbonFactor, on_delete=models.CASCADE, related_name='emission_records')
    
    energy_joules = models.FloatField()
    energy_kwh = models.FloatField()
    carbon_emissions_g = models.FloatField(help_text="Direct carbon emissions in grams CO2e")
    carbon_emissions_kg = models.FloatField(help_text="Carbon emissions in kilograms CO2e")
    annualized_emissions_kg = models.FloatField(default=0.0, help_text="Projected annual emissions at 10M requests")
    
    carbon_score = models.FloatField(default=85.0, help_text="Carbon efficiency score (0-100)")
    confidence_score = models.FloatField(default=95.0)

    class Meta:
        verbose_name = "Carbon Emission Record"
        verbose_name_plural = "Carbon Emission Records"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.library.library_name} @ {self.regional_grid.region_code} -> {self.carbon_emissions_g:.4f} gCO2e"


class CarbonSavingsEstimate(TimeStampedModel):
    """Quantifies environmental savings when migrating from a source library to a greener alternative."""
    source_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='savings_as_source')
    target_library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='savings_as_target')
    regional_grid = models.ForeignKey(RegionalGridCarbonFactor, on_delete=models.CASCADE, related_name='savings_estimates')
    
    requests_per_year = models.BigIntegerField(default=10000000, help_text="Annual execution traffic volume")
    energy_saved_kwh = models.FloatField(help_text="Annual energy saved in kWh")
    carbon_saved_kg = models.FloatField(help_text="Annual CO2e avoided in kg")
    carbon_reduction_pct = models.FloatField(help_text="Percentage reduction in emissions")
    
    # Environmental equivalencies
    trees_equivalent = models.FloatField(help_text="Equivalent urban tree seedlings grown for 10 years")
    vehicle_km_avoided = models.FloatField(help_text="Equivalent passenger vehicle kilometers avoided")
    cost_saved_usd = models.FloatField(help_text="Estimated electricity cost saved in USD ($0.14/kWh)")
    
    explanation_narrative = models.TextField(help_text="Explainable sustainability justification")

    class Meta:
        verbose_name = "Carbon Savings Estimate"
        verbose_name_plural = "Carbon Savings Estimates"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source_library.library_name} -> {self.target_library.library_name}: -{self.carbon_saved_kg:.1f} kg CO2e ({self.carbon_reduction_pct:.1f}%)"


class CarbonImpactReport(TimeStampedModel):
    """Executive environmental sustainability impact report."""
    title = models.CharField(max_length=200)
    total_libraries_audited = models.PositiveIntegerField(default=0)
    total_energy_kwh = models.FloatField(default=0.0)
    total_carbon_kg = models.FloatField(default=0.0)
    baseline_savings_potential_kg = models.FloatField(default=0.0)
    summary_metrics = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Carbon Impact Report"
        verbose_name_plural = "Carbon Impact Reports"
        ordering = ['-created_at']


class CarbonForecast(TimeStampedModel):
    """Simulates multi-month software carbon emissions under traffic growth curves."""
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='carbon_forecasts')
    regional_grid = models.ForeignKey(RegionalGridCarbonFactor, on_delete=models.CASCADE, related_name='forecasts')
    forecast_horizon_months = models.PositiveIntegerField(default=12)
    projected_monthly_emissions_kg = models.JSONField(default=list, help_text="12-month array of projected monthly emissions")
    trend_slope = models.FloatField(default=0.0)
    confidence_interval = models.FloatField(default=95.0)

    class Meta:
        verbose_name = "Carbon Forecast"
        verbose_name_plural = "Carbon Forecasts"
        ordering = ['-created_at']
