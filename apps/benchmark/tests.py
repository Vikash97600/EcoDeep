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
from apps.benchmark.services.sampling_manager import ContinuousSamplerThread
from apps.benchmark.plugins.cpu_plugin import CpuMeasurementPlugin
from apps.benchmark.plugins.memory_plugin import MemoryMeasurementPlugin

class ResourceMeasurementTestCase(TestCase):
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

        self.session = BenchmarkSession.objects.create(session_name="Resource Measurement Session", status=BenchmarkStatusChoices.COMPLETED)
        self.result = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver, task=self.task, dataset=self.dataset, iterations=50
        )

    def test_continuous_sampling_thread(self):
        sampler = ContinuousSamplerThread(interval_sec=0.01)
        sampler.start()
        time.sleep(0.05)
        sampler.stop()
        self.assertGreater(len(sampler.cpu_samples), 0)
        self.assertGreater(len(sampler.memory_samples_mb), 0)

    def test_tracemalloc_memory_profiling(self):
        tracemalloc.start()
        dummy_data = [i for i in range(100000)]
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.assertGreater(peak, 0)

    def test_cpu_plugin_execution(self):
        plugin = CpuMeasurementPlugin()
        self.assertEqual(plugin.name, 'cpu_plugin')
        plugin.start()
        time.sleep(0.05)
        metrics = plugin.stop()
        self.assertIn('average_cpu', metrics)
        self.assertIn('peak_cpu', metrics)

    def test_memory_plugin_execution(self):
        plugin = MemoryMeasurementPlugin()
        self.assertEqual(plugin.name, 'memory_plugin')
        plugin.start()
        dummy_data = [x * 2 for x in range(50000)]
        metrics = plugin.stop()
        self.assertIn('peak_memory', metrics)
        self.assertIn('rss_memory_mb', metrics)
