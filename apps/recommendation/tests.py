from django.test import TestCase, Client
from apps.benchmark.models import BenchmarkSession, BenchmarkTask, BenchmarkDataset, BenchmarkResult, BenchmarkStatusChoices
from apps.libraries.models import ProgrammingLanguage, Category, Library, LibraryVersion
from apps.recommendation.models import GreenScore, WeightProfile, ScoringStrategyChoices
from apps.recommendation.services.normalization_service import NormalizationService
from apps.recommendation.services.strategies.weighted_sum import WeightedSumStrategy
from apps.recommendation.services.strategies.weighted_product import WeightedProductStrategy
from apps.recommendation.services.strategies.topsis import TopsisStrategy
from apps.recommendation.services.greenscore_service import GreenScoreService

class GreenScoreEngineTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.lang = ProgrammingLanguage.objects.create(language_name="Python", slug="python")
        self.cat = Category.objects.create(category_name="Data Serialization", slug="data-serialization", description="JSON parsers")

        self.dataset = BenchmarkDataset.objects.create(
            dataset_name="10MB JSON Payload", dataset_category=self.cat, dataset_size_bytes=10485760, description="Test dataset"
        )
        self.task = BenchmarkTask.objects.create(
            task_name="JSON Deserialization 10MB", category=self.cat, dataset=self.dataset, description="Workload task", iterations=50
        )
        self.lib1 = Library.objects.create(library_name="json", official_name="Python stdlib json", programming_language=self.lang, category=self.cat, description="Stdlib JSON")
        self.ver1 = LibraryVersion.objects.create(library=self.lib1, version_number="3.11.4")

        self.lib2 = Library.objects.create(library_name="orjson", official_name="orjson Fast JSON", programming_language=self.lang, category=self.cat, description="Fast C JSON")
        self.ver2 = LibraryVersion.objects.create(library=self.lib2, version_number="3.9.1")

        self.session = BenchmarkSession.objects.create(session_name="GreenScore Session", status=BenchmarkStatusChoices.COMPLETED)
        
        self.res1 = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver1, task=self.task, dataset=self.dataset, execution_time=100.0, average_cpu=15.0, peak_memory=50.0, energy=20.0, co2=0.005
        )
        self.res2 = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver2, task=self.task, dataset=self.dataset, execution_time=25.0, average_cpu=10.0, peak_memory=20.0, energy=5.0, co2=0.001
        )

        self.profile = WeightProfile.objects.create(
            profile_name="Balanced Test Profile",
            weight_execution_time=0.30,
            weight_cpu_usage=0.20,
            weight_peak_memory=0.20,
            weight_energy=0.20,
            weight_co2=0.10,
            is_default=True
        )

    def test_inverse_min_max_normalization(self):
        data = [
            {'result_id': 1, 'execution_time': 100.0, 'cpu_usage': 15.0, 'peak_memory': 50.0, 'energy': 20.0, 'co2': 0.005},
            {'result_id': 2, 'execution_time': 25.0, 'cpu_usage': 10.0, 'peak_memory': 20.0, 'energy': 5.0, 'co2': 0.001}
        ]
        norm = NormalizationService.normalize_results(data)
        # Faster/cleaner package 2 should get 1.0 for all cost metrics
        self.assertEqual(norm[2]['execution_time'], 1.0)
        self.assertEqual(norm[1]['execution_time'], 0.0)

    def test_weighted_sum_strategy(self):
        norm_matrix = {
            1: {'execution_time': 0.0, 'cpu_usage': 0.0, 'peak_memory': 0.0, 'energy': 0.0, 'co2': 0.0},
            2: {'execution_time': 1.0, 'cpu_usage': 1.0, 'peak_memory': 1.0, 'energy': 1.0, 'co2': 1.0}
        }
        weights = {'weight_execution_time': 0.3, 'weight_cpu_usage': 0.2, 'weight_peak_memory': 0.2, 'weight_energy': 0.2, 'weight_co2': 0.1}
        wsm = WeightedSumStrategy()
        scores = wsm.compute_scores(norm_matrix, weights)
        self.assertEqual(scores[2], 1.0)
        self.assertEqual(scores[1], 0.0)

    def test_topsis_strategy(self):
        norm_matrix = {
            1: {'execution_time': 0.0, 'cpu_usage': 0.0, 'peak_memory': 0.0, 'energy': 0.0, 'co2': 0.0},
            2: {'execution_time': 1.0, 'cpu_usage': 1.0, 'peak_memory': 1.0, 'energy': 1.0, 'co2': 1.0}
        }
        weights = {'weight_execution_time': 0.3, 'weight_cpu_usage': 0.2, 'weight_peak_memory': 0.2, 'weight_energy': 0.2, 'weight_co2': 0.1}
        topsis = TopsisStrategy()
        scores = topsis.compute_scores(norm_matrix, weights)
        self.assertGreater(scores[2], scores[1])

    def test_greenscore_service_session_calculation(self):
        scores = GreenScoreService.calculate_session_greenscores(
            session_id=self.session.id, strategy_name='TOPSIS', profile_name=self.profile.profile_name
        )
        self.assertEqual(len(scores), 2)
        gs_orjson = GreenScore.objects.get(result=self.res2)
        gs_json = GreenScore.objects.get(result=self.res1)
        self.assertGreater(gs_orjson.score, gs_json.score)
