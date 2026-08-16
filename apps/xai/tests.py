from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.users.models import Role, RoleChoices, UserProfile
from apps.libraries.models import ProgrammingLanguage, Category, Library
from apps.xai.models import (
    RecommendationExplanation, FeatureContribution, SHAPAttributionResult,
    CounterfactualScenario, DecisionTraceAudit, TrustScoreRecord, ExplanationTypeChoices, PersonaTypeChoices
)
from apps.xai.services.shap_service import SHAPService
from apps.xai.services.counterfactual_service import CounterfactualService
from apps.xai.services.why_not_service import WhyNotService
from apps.xai.services.comparative_explanation_service import ComparativeExplanationService
from apps.xai.services.traceability_service import TraceabilityService
from apps.xai.services.trust_service import TrustService
from apps.xai.services.xai_orchestrator_service import XAIOrchestratorService

class XAITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.user = User.objects.create_user(username='xai_user', password='Password123!')
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

    def test_shap_service(self):
        shap_res = SHAPService.calculate_shap_values(self.lib_b, {})
        self.assertIsNotNone(shap_res)
        self.assertIn('energy_joules', shap_res.shap_values_json)
        self.assertGreater(len(shap_res.top_contributing_features), 0)

    def test_counterfactual_service(self):
        scenarios = CounterfactualService.generate_counterfactuals(self.lib_a, current_rank=2, current_score=72.0)
        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[0].resulting_rank, 1)

    def test_why_not_service(self):
        exp = WhyNotService.explain_why_not(self.lib_a, self.lib_b, score_diff=18.5)
        self.assertIsNotNone(exp)
        self.assertEqual(exp.explanation_type, ExplanationTypeChoices.WHY_NOT_RECOMMENDED)

    def test_comparative_service(self):
        comp = ComparativeExplanationService.generate_comparison_explanation(self.lib_a, self.lib_b, 28.0, 35.0)
        self.assertIsNotNone(comp)
        self.assertEqual(comp.explanation_type, ExplanationTypeChoices.COMPARATIVE)

    def test_traceability_service(self):
        trace = TraceabilityService.create_decision_trace(self.lib_b)
        self.assertIsNotNone(trace)
        self.assertEqual(len(trace.trace_hash_sha256), 64)

    def test_trust_service(self):
        trust = TrustService.evaluate_trust_score(self.lib_b)
        self.assertIsNotNone(trust)
        self.assertGreaterEqual(trust.overall_trust_score, 80.0)

    def test_xai_orchestrator_packet(self):
        packet = XAIOrchestratorService.generate_full_explanation_packet(self.lib_b, persona=PersonaTypeChoices.DEVELOPER)
        self.assertIn('explanation', packet)
        self.assertIn('shap_result', packet)
        self.assertIn('counterfactuals', packet)
        self.assertIn('trace', packet)
        self.assertIn('trust_score', packet)

    def test_xai_views(self):
        self.client.login(username='xai_user', password='Password123!')

        res_dash = self.client.get(reverse('xai:dashboard'))
        self.assertEqual(res_dash.status_code, 200)

        res_studio = self.client.get(reverse('xai:explanation_studio'))
        self.assertEqual(res_studio.status_code, 200)

        res_sand = self.client.get(reverse('xai:counterfactual_sandbox'))
        self.assertEqual(res_sand.status_code, 200)

        res_why = self.client.get(reverse('xai:why_not_analysis'))
        self.assertEqual(res_why.status_code, 200)

        res_trace = self.client.get(reverse('xai:decision_trace'))
        self.assertEqual(res_trace.status_code, 200)

        res_trust = self.client.get(reverse('xai:trust_scoreboard'))
        self.assertEqual(res_trust.status_code, 200)
