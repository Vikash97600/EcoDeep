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
from apps.benchmark.plugins.energy_plugin import EnergyMeasurementPlugin
from apps.benchmark.plugins.energy.manager import EnergyManager
from apps.benchmark.plugins.energy.rapl_provider import IntelRaplProvider
from apps.benchmark.plugins.energy.codecarbon_provider import CodeCarbonProvider

class EnergyMeasurementTestCase(TestCase):
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

        self.session = BenchmarkSession.objects.create(session_name="Energy Measurement Session", status=BenchmarkStatusChoices.COMPLETED)
        self.result = BenchmarkResult.objects.create(
            session=self.session, library_version=self.ver, task=self.task, dataset=self.dataset, iterations=50, energy=15.5, co2=0.002
        )

    def test_energy_manager_provider_selection(self):
        provider = EnergyManager.get_best_provider()
        self.assertIsNotNone(provider)
        self.assertIn(provider.name, ['intel_rapl', 'codecarbon', 'scaphandre'])

    def test_joules_to_kwh_conversion(self):
        energy_joules = 3600000.0  # 3.6 million Joules = 1 kWh
        energy_kwh = energy_joules / 3.6e6
        self.assertEqual(energy_kwh, 1.0)

    def test_energy_plugin_execution(self):
        plugin = EnergyMeasurementPlugin()
        self.assertEqual(plugin.name, 'energy_plugin')
        plugin.start()
        time.sleep(0.02)
        metrics = plugin.stop()
        self.assertIn('energy_joules', metrics)
        self.assertIn('co2_grams', metrics)
