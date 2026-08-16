from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.users.models import Role, RoleChoices, UserProfile
from apps.libraries.models import ProgrammingLanguage, Category, Library
from apps.mcdm.models import (
    MCDMWeightProfile, MCDMEvaluationRun, GreenScoreRecord, MCDMMethodChoices, ProfileTypeChoices
)
from apps.mcdm.services.normalization_service import NormalizationService
from apps.mcdm.services.weight_service import WeightService
from apps.mcdm.services.wsm_service import WSMService
from apps.mcdm.services.wpm_service import WPMService
from apps.mcdm.services.topsis_service import TOPSService
from apps.mcdm.services.ahp_service import AHPService
from apps.mcdm.services.greenscore_service import GreenScoreService
from apps.mcdm.services.sensitivity_service import SensitivityService
from apps.mcdm.services.ranking_service import RankingService

class MCDMTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.user = User.objects.create_user(username='mcdm_user', password='Password123!')
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

        WeightService.get_or_create_default_profiles()
        self.profile = MCDMWeightProfile.objects.filter(is_default=True).first()

    def test_normalization_service(self):
        matrix = [
            {'library_id': 1, 'library_name': 'libA', 'energy_joules': 2.0, 'execution_time_ms': 40.0, 'cpu_utilization_pct': 10.0, 'ram_rss_mb': 20.0, 'co2_emissions_g': 0.5},
            {'library_id': 2, 'library_name': 'libB', 'energy_joules': 5.0, 'execution_time_ms': 80.0, 'cpu_utilization_pct': 20.0, 'ram_rss_mb': 40.0, 'co2_emissions_g': 1.2}
        ]
        norm = NormalizationService.vector_normalize(matrix)
        self.assertEqual(len(norm), 2)
        self.assertGreater(norm[0]['energy_joules'], 0.0)

    def test_topsis_wsm_wpm_services(self):
        matrix = [
            {'library_id': 1, 'library_name': 'libA', 'energy_joules': 2.0, 'execution_time_ms': 40.0, 'cpu_utilization_pct': 10.0, 'ram_rss_mb': 20.0, 'co2_emissions_g': 0.5},
            {'library_id': 2, 'library_name': 'libB', 'energy_joules': 5.0, 'execution_time_ms': 80.0, 'cpu_utilization_pct': 20.0, 'ram_rss_mb': 40.0, 'co2_emissions_g': 1.2}
        ]
        weights = {'energy_joules': 0.35, 'execution_time_ms': 0.25, 'cpu_utilization_pct': 0.15, 'ram_rss_mb': 0.15, 'co2_emissions_g': 0.10}

        topsis_res = TOPSService.calculate_topsis(matrix, weights)
        self.assertEqual(len(topsis_res), 2)
        # libA is lower in all cost metrics -> should be #1 with higher closeness
        self.assertEqual(topsis_res[0]['library_name'], 'libA')
        self.assertGreater(topsis_res[0]['closeness_coefficient'], topsis_res[1]['closeness_coefficient'])

        cost_norm = NormalizationService.min_max_cost_normalize(matrix)
        wsm_res = WSMService.calculate_wsm(cost_norm, weights)
        self.assertEqual(wsm_res[0]['library_name'], 'libA')

        wpm_res = WPMService.calculate_wpm(cost_norm, weights)
        self.assertEqual(wpm_res[0]['library_name'], 'libA')

    def test_ahp_service(self):
        matrix = AHPService.get_default_ahp_matrix()
        weights, ci, cr, is_consistent = AHPService.calculate_ahp_weights(matrix)
        self.assertTrue(is_consistent)
        self.assertLess(cr, 0.10)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=2)

    def test_end_to_end_ranking_and_sensitivity(self):
        eval_run = RankingService.execute_mcdm_ranking(category=self.cat, profile=self.profile, method=MCDMMethodChoices.TOPSIS)
        self.assertIsNotNone(eval_run)
        self.assertEqual(eval_run.green_score_records.count(), 2)
        
        top_rec = eval_run.green_score_records.first()
        self.assertEqual(top_rec.rank_position, 1)
        self.assertGreater(top_rec.green_score, 0.0)

        report = SensitivityService.audit_ranking_sensitivity(eval_run, criterion_to_perturb='energy_joules', perturbation_pct=20.0)
        self.assertIsNotNone(report)
        self.assertGreaterEqual(report.spearman_rho, 0.0)

    def test_mcdm_views(self):
        self.client.login(username='mcdm_user', password='Password123!')

        res_dash = self.client.get(reverse('mcdm:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_studio = self.client.get(reverse('mcdm:ranking_studio'))
        self.assertEqual(res_studio.status_code, 200)

        res_prof = self.client.get(reverse('mcdm:weight_profiles'))
        self.assertEqual(res_prof.status_code, 200)

        res_ahp = self.client.get(reverse('mcdm:ahp_calculator'))
        self.assertEqual(res_ahp.status_code, 200)

        res_sens = self.client.get(reverse('mcdm:sensitivity_analysis'))
        self.assertEqual(res_sens.status_code, 200)
