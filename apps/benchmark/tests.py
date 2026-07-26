import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.benchmark.models import BenchmarkSession, BenchmarkTask, BenchmarkDataset, BenchmarkJob, BenchmarkResult, RawExecutionSample, BenchmarkStatusChoices
from apps.libraries.models import ProgrammingLanguage, Category, Library, LibraryVersion
from apps.users.models import Role, RoleChoices, UserProfile
from apps.benchmark.services.statistics_service import StatisticalAnalysisService
from apps.benchmark.plugins.execution_time_plugin import ExecutionTimePlugin

class ScientificExecutionTimeTestCase(TestCase):
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
        self.lib = Library.objects.create(
            library_name="orjson", official_name="orjson Fast JSON", programming_language=self.lang, category=self.cat, description="Fast JSON"
        )
        self.ver = LibraryVersion.objects.create(library=self.lib, version_number="3.9.1")

        self.session = BenchmarkSession.objects.create(session_name="Time Measurement Session", status=BenchmarkStatusChoices.COMPLETED)
        self.result = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver, task=self.task, dataset=self.dataset, iterations=50
        )

    def test_high_resolution_timer(self):
        t1 = time.perf_counter_ns()
        time.sleep(0.001)
        t2 = time.perf_counter_ns()
        delta_ns = t2 - t1
        self.assertGreater(delta_ns, 0)
        self.assertIsInstance(delta_ns, int)

    def test_iqr_outlier_filtering(self):
        # 10 normal samples around 100ms (100,000,000 ns) and 1 outlier at 500ms
        samples = [100000000 + i*1000 for i in range(10)] + [500000000]
        valid, outliers = StatisticalAnalysisService.filter_outliers_iqr(samples)
        self.assertEqual(len(outliers), 1)
        self.assertEqual(outliers[0], 500000000)
        self.assertEqual(len(valid), 10)

    def test_statistical_analysis_service(self):
        samples = [100000000, 102000000, 98000000, 101000000, 99000000]
        stats = StatisticalAnalysisService.calculate_statistics(samples)
        self.assertIn('mean_ms', stats)
        self.assertIn('ci_95_lower_ms', stats)
        self.assertIn('ci_95_upper_ms', stats)
        self.assertGreater(stats['mean_ms'], 0)

    def test_execution_time_plugin_registration(self):
        plugin = ExecutionTimePlugin()
        self.assertEqual(plugin.name, 'execution_time_plugin')
        plugin.start()
        plugin.record_sample(1000, 2000)
        metrics = plugin.stop()
        self.assertIn('total_elapsed_ms', metrics)
