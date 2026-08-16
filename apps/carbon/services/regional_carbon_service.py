from apps.carbon.models import RegionalGridCarbonFactor, CloudProviderChoices

class RegionalCarbonService:
    """Manages regional electrical grid carbon intensity factors (gCO2/kWh) and PUE defaults."""

    DEFAULT_REGIONS = [
        {
            'region_code': 'us-east-1',
            'region_name': 'US East (N. Virginia)',
            'provider': CloudProviderChoices.AWS,
            'country': 'United States',
            'carbon_intensity_g_per_kwh': 379.0,
            'pue_factor': 1.15,
            'renewable_share_pct': 32.0,
            'is_default': True
        },
        {
            'region_code': 'eu-west-1',
            'region_name': 'Europe (Ireland)',
            'provider': CloudProviderChoices.AWS,
            'country': 'Ireland',
            'carbon_intensity_g_per_kwh': 288.0,
            'pue_factor': 1.12,
            'renewable_share_pct': 45.0,
            'is_default': False
        },
        {
            'region_code': 'eu-north-1',
            'region_name': 'Europe (Stockholm, Sweden)',
            'provider': CloudProviderChoices.AWS,
            'country': 'Sweden',
            'carbon_intensity_g_per_kwh': 28.0,
            'pue_factor': 1.10,
            'renewable_share_pct': 92.0,
            'is_default': False
        },
        {
            'region_code': 'ap-south-1',
            'region_name': 'Asia Pacific (Mumbai, India)',
            'provider': CloudProviderChoices.AWS,
            'country': 'India',
            'carbon_intensity_g_per_kwh': 708.0,
            'pue_factor': 1.25,
            'renewable_share_pct': 22.0,
            'is_default': False
        },
        {
            'region_code': 'global-avg',
            'region_name': 'Global Average Grid Baseline',
            'provider': CloudProviderChoices.NATIONAL_GRID,
            'country': 'Global',
            'carbon_intensity_g_per_kwh': 436.0,
            'pue_factor': 1.20,
            'renewable_share_pct': 30.0,
            'is_default': False
        }
    ]

    @staticmethod
    def get_or_create_default_regions():
        """Ensures standard regional cloud grid carbon factors exist in the database."""
        for r in RegionalCarbonService.DEFAULT_REGIONS:
            RegionalGridCarbonFactor.objects.get_or_create(
                region_code=r['region_code'],
                defaults=r
            )

    @staticmethod
    def get_default_region() -> RegionalGridCarbonFactor:
        """Returns default or fallback regional grid."""
        RegionalCarbonService.get_or_create_default_regions()
        return RegionalGridCarbonFactor.objects.filter(is_default=True).first() or RegionalGridCarbonFactor.objects.first()
