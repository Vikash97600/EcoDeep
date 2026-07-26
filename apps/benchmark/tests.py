import time
import tracemalloc
import psutil
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.benchmark.models import BenchmarkSession, BenchmarkTask, BenchmarkDataset, BenchmarkJob, BenchmarkResult, RawExecutionSample, BenchmarkStatusChoices
from apps.libraries.models import ProgrammingLanguage, Category, Library, LibraryVersion
from apps.users.models import Role, RoleChoices, UserProfile
from apps.benchmark.services.statistics_service import StatisticalAnalysisService
from apps.benchmark.services.validation_service import ValidationService
from apps.benchmark.services.repository_service import RepositoryService
from apps.benchmark.services.comparison_service import ComparisonService
from apps.benchmark.services.export_service import ExportService

class ResearchRepositoryTestCase(TestCase):
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

        self.session = BenchmarkSession.objects.create(session_name="Repository Session", status=BenchmarkStatusChoices.COMPLETED)
        
        self.res1 = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver1, task=self.task, dataset=self.dataset, execution_time=100.0, energy=20.0, co2=0.005
        )
        self.res2 = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver2, task=self.task, dataset=self.dataset, execution_time=25.0, energy=5.0, co2=0.001
        )

    def test_validation_service(self):
        is_valid, errors = ValidationService.validate_metrics(100.0, 15.0, 32.0, 10.0)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        is_valid, errors = ValidationService.validate_metrics(-5.0, 15.0, 32.0, 10.0)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_repository_service_filtering(self):
        results = RepositoryService.filter_repository(category_id=self.cat.id)
        self.assertEqual(results.count(), 2)

        results = RepositoryService.filter_repository(search_query="orjson")
        self.assertEqual(results.count(), 1)

    def test_comparison_service_deltas(self):
        comp = ComparisonService.compare_results([self.res1.id, self.res2.id])
        self.assertIn('comparisons', comp)
        self.assertEqual(len(comp['comparisons']), 2)
        # Verify orjson time delta is -75.0% (4x faster)
        orjson_comp = comp['comparisons'][1]
        self.assertEqual(orjson_comp['time_delta_pct'], -75.0)

    def test_repository_csv_export(self):
        response = ExportService.export_repository_csv(BenchmarkResult.objects.all())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
