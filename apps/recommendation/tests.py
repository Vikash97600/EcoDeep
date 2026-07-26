from django.test import TestCase, Client
from django.urls import reverse
from apps.benchmark.models import BenchmarkSession, BenchmarkTask, BenchmarkDataset, BenchmarkResult, BenchmarkStatusChoices
from apps.libraries.models import ProgrammingLanguage, Category, Library, LibraryVersion
from apps.recommendation.models import GreenScore, WeightProfile, ScoringStrategyChoices, RecommendationRecord, RecommendationProfileChoices
from apps.recommendation.services.normalization_service import NormalizationService
from apps.recommendation.services.strategies.weighted_sum import WeightedSumStrategy
from apps.recommendation.services.strategies.weighted_product import WeightedProductStrategy
from apps.recommendation.services.strategies.topsis import TopsisStrategy
from apps.recommendation.services.greenscore_service import GreenScoreService
from apps.recommendation.services.similarity_service import SimilarityService
from apps.recommendation.services.constraint_service import ConstraintService
from apps.recommendation.services.recommendation_service import RecommendationService

class IntelligentRecommendationTestCase(TestCase):
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

        self.session = BenchmarkSession.objects.create(session_name="Recommendation Session", status=BenchmarkStatusChoices.COMPLETED)
        
        self.res1 = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver1, task=self.task, dataset=self.dataset, execution_time=100.0, average_cpu=15.0, peak_memory=50.0, energy=20.0, co2=0.005, green_score=62.10
        )
        self.res2 = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver2, task=self.task, dataset=self.dataset, execution_time=25.0, average_cpu=10.0, peak_memory=20.0, energy=5.0, co2=0.001, green_score=93.40
        )

    def test_similarity_discovery(self):
        equivalents = SimilarityService.get_equivalent_libraries(self.lib1)
        self.assertIn(self.lib2, equivalents)

    def test_constraint_filtering(self):
        filtered = ConstraintService.filter_candidates([self.lib1, self.lib2], required_language=self.lang)
        self.assertEqual(len(filtered), 2)

    def test_recommendation_generation(self):
        rec_record = RecommendationService.generate_recommendation(
            target_library_id=self.lib1.id,
            task_id=self.task.id,
            profile_type=RecommendationProfileChoices.BEST_OVERALL
        )
        self.assertIsNotNone(rec_record)
        self.assertEqual(rec_record.items.count(), 2)

        top_choice = rec_record.items.filter(is_top_choice=True).first()
        self.assertEqual(top_choice.recommended_version, self.ver2)
        self.assertIn("75.0% faster", top_choice.explanation_text)

    def test_api_recommendation_query(self):
        response = self.client.get(reverse('recommendation:api_recommend_query'), {
            'target_library': self.lib1.id,
            'task': self.task.id,
            'profile': 'BEST_OVERALL'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('recommendations', data)
        self.assertEqual(len(data['recommendations']), 2)
