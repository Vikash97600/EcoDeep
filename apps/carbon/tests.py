from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.users.models import Role, RoleChoices, UserProfile
from apps.libraries.models import ProgrammingLanguage, Category, Library
from apps.carbon.models import (
    RegionalGridCarbonFactor, CarbonEmissionRecord, CarbonSavingsEstimate, CarbonForecast
)
from apps.carbon.services.regional_carbon_service import RegionalCarbonService
from apps.carbon.services.carbon_service import CarbonService
from apps.carbon.services.carbon_savings_service import CarbonSavingsService
from apps.carbon.services.carbon_comparison_service import CarbonComparisonService
from apps.carbon.services.carbon_forecast_service import CarbonForecastService

class CarbonIntelligenceTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.user = User.objects.create_user(username='carbon_user', password='Password123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.role = self.researcher_role
        profile.save()

        self.lang = ProgrammingLanguage.objects.create(language_name='Python', slug='python')
        self.cat = Category.objects.create(category_name='JSON Parsers', slug='json-parsers')

        self.lib_a = Library.objects.create(
            library_name='json_std',
            official_name='json',
            current_version='3.11.0',
            programming_language=self.lang,
            category=self.cat
        )
        self.lib_b = Library.objects.create(
            library_name='ujson_fast',
            official_name='ujson',
            current_version='5.7.0',
            programming_language=self.lang,
            category=self.cat
        )

        RegionalCarbonService.get_or_create_default_regions()
        self.grid = RegionalCarbonService.get_default_region()

    def test_regional_carbon_service(self):
        self.assertIsNotNone(self.grid)
        self.assertGreater(self.grid.carbon_intensity_g_per_kwh, 0.0)
        self.assertGreaterEqual(self.grid.pue_factor, 1.0)

    def test_carbon_calculation_service(self):
        # 3.6 MJ = 1 kWh -> at 379 g/kWh * 1.15 PUE = 435.85 gCO2e
        energy_j = 3600000.0
        metrics = CarbonService.calculate_emissions(energy_j, self.grid)
        self.assertEqual(metrics['energy_kwh'], 1.0)
        self.assertAlmostEqual(metrics['carbon_emissions_g'], 379.0 * 1.15, places=2)

        record = CarbonService.record_library_carbon(self.lib_a, energy_joules=5.80, grid=self.grid)
        self.assertIsNotNone(record)
        self.assertGreater(record.carbon_emissions_g, 0.0)

    def test_carbon_savings_and_equivalencies(self):
        estimate = CarbonSavingsService.calculate_savings(
            source_lib=self.lib_a,
            target_lib=self.lib_b,
            source_energy_joules=5.80,
            target_energy_joules=2.15,
            grid=self.grid,
            requests_per_year=10000000
        )
        self.assertIsNotNone(estimate)
        self.assertGreater(estimate.carbon_saved_kg, 0.0)
        self.assertGreater(estimate.trees_equivalent, 0.0)
        self.assertGreater(estimate.vehicle_km_avoided, 0.0)
        self.assertGreater(estimate.cost_saved_usd, 0.0)

    def test_carbon_comparison_service(self):
        comp = CarbonComparisonService.compare_libraries(self.lib_a, self.lib_b, self.grid)
        self.assertIsNotNone(comp)
        self.assertEqual(comp['recommended_library'], 'ujson_fast')
        self.assertGreater(comp['percentage_reduction'], 0.0)

    def test_carbon_forecast_service(self):
        forecast = CarbonForecastService.generate_12_month_forecast(self.lib_a, self.grid)
        self.assertIsNotNone(forecast)
        self.assertEqual(len(forecast.projected_monthly_emissions_kg), 12)
        # Month 12 emissions should be greater than Month 1 due to 5% MoM growth
        self.assertGreater(forecast.projected_monthly_emissions_kg[11]['carbon_kg'], forecast.projected_monthly_emissions_kg[0]['carbon_kg'])

    def test_carbon_views(self):
        self.client.login(username='carbon_user', password='Password123!')

        res_dash = self.client.get(reverse('carbon:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_grids = self.client.get(reverse('carbon:regional_grids'))
        self.assertEqual(res_grids.status_code, 200)

        res_comp = self.client.get(reverse('carbon:comparison_studio'))
        self.assertEqual(res_comp.status_code, 200)

        res_sav = self.client.get(reverse('carbon:savings_calculator'))
        self.assertEqual(res_sav.status_code, 200)

        res_fore = self.client.get(reverse('carbon:carbon_forecast'))
        self.assertEqual(res_fore.status_code, 200)
