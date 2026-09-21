from django.test import Client, TestCase
from django.urls import reverse

from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkStatusChoices,
    BenchmarkTask,
)
from apps.libraries.models import Category, Library, LibraryVersion, ProgrammingLanguage
from apps.recommendation.models import (
    RecommendationProfileChoices,
)
from apps.recommendation.services.constraint_service import ConstraintService
from apps.recommendation.services.recommendation_service import RecommendationService
from apps.recommendation.services.similarity_service import SimilarityService


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


from apps.recommendation.services.greenscore_service import GreenScoreService


class GreenScoreRegressionTestCase(TestCase):
    def setUp(self):
        self.lang = ProgrammingLanguage.objects.create(language_name="Python", slug="py-gs")
        self.cat = Category.objects.create(category_name="JSON GS Test", slug="json-gs-test")
        self.dataset = BenchmarkDataset.objects.create(dataset_name="GS DS", dataset_category=self.cat, dataset_size_bytes=1000)
        self.task = BenchmarkTask.objects.create(task_name="GS Task", category=self.cat, dataset=self.dataset)

    def test_greenscore_continuous_variation(self):
        """Verify that candidates with varying physical metrics receive non-identical, continuous Green Scores."""
        session = BenchmarkSession.objects.create(session_name="GS Variation Session", status=BenchmarkStatusChoices.COMPLETED)
        
        libs = []
        for i in range(4):
            l = Library.objects.create(library_name=f"lib_gs_{i}", category=self.cat, programming_language=self.lang)
            v = LibraryVersion.objects.create(library=l, version_number="1.0")
            libs.append(v)

        # Create distinct metric profiles
        # Candidate 0: Fastest, lowest energy
        BenchmarkResult.objects.create(session=session, library_version=libs[0], task=self.task, dataset=self.dataset, execution_time=10.0, average_cpu=10.0, peak_memory=15.0, energy=2.0, co2=0.0001)
        # Candidate 1: Slightly slower
        BenchmarkResult.objects.create(session=session, library_version=libs[1], task=self.task, dataset=self.dataset, execution_time=25.0, average_cpu=20.0, peak_memory=30.0, energy=5.0, co2=0.0005)
        # Candidate 2: Medium
        BenchmarkResult.objects.create(session=session, library_version=libs[2], task=self.task, dataset=self.dataset, execution_time=60.0, average_cpu=40.0, peak_memory=55.0, energy=12.0, co2=0.0020)
        # Candidate 3: Slowest, highest energy
        BenchmarkResult.objects.create(session=session, library_version=libs[3], task=self.task, dataset=self.dataset, execution_time=150.0, average_cpu=75.0, peak_memory=95.0, energy=35.0, co2=0.0080)

        gs_objs = GreenScoreService.calculate_session_greenscores(session.id)
        scores = [obj.score for obj in gs_objs]

        self.assertEqual(len(scores), 4)
        # Scores must all be distinct
        self.assertEqual(len(set(scores)), 4, f"Scores collapsed to fixed values: {scores}")
        # Scores must strictly follow performance rank (Candidate 0 > Candidate 1 > Candidate 2 > Candidate 3)
        self.assertTrue(scores[0] > scores[1] > scores[2] > scores[3], f"Score ordering incorrect: {scores}")

    def test_greenscore_determinism_and_session_isolation(self):
        """Verify identical inputs yield identical scores and session scores do not contaminate across sessions."""
        session1 = BenchmarkSession.objects.create(session_name="Session 1", status=BenchmarkStatusChoices.COMPLETED)
        session2 = BenchmarkSession.objects.create(session_name="Session 2", status=BenchmarkStatusChoices.COMPLETED)

        lib1 = Library.objects.create(library_name="lib_iso_1", category=self.cat, programming_language=self.lang)
        ver1 = LibraryVersion.objects.create(library=lib1, version_number="1.0")

        BenchmarkResult.objects.create(session=session1, library_version=ver1, task=self.task, dataset=self.dataset, execution_time=20.0, average_cpu=20.0, peak_memory=30.0, energy=4.0, co2=0.0004)
        BenchmarkResult.objects.create(session=session2, library_version=ver1, task=self.task, dataset=self.dataset, execution_time=20.0, average_cpu=20.0, peak_memory=30.0, energy=4.0, co2=0.0004)

        gs1 = GreenScoreService.calculate_session_greenscores(session1.id)[0]
        gs2 = GreenScoreService.calculate_session_greenscores(session2.id)[0]

        self.assertEqual(gs1.score, gs2.score)

