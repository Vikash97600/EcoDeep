from django.test import Client, TestCase
from django.urls import reverse

from apps.plugins.models import PluginManifest
from apps.plugins.sample_plugins.csv_export_plugin import CSVExportPlugin
from apps.plugins.sample_plugins.energy_measurement_plugin import (
    EnergyMeasurementPlugin,
)
from apps.plugins.sample_plugins.python_benchmark_plugin import PythonBenchmarkPlugin
from apps.plugins.services.plugin_event_service import PluginEventService
from apps.plugins.services.plugin_loader_service import PluginLoaderService
from apps.plugins.services.plugin_registry_service import PluginRegistryService


class PluginSDKFrameworkTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.py_manifest = PluginRegistryService.register_plugin_class(PythonBenchmarkPlugin, is_system_plugin=True)
        self.energy_manifest = PluginRegistryService.register_plugin_class(EnergyMeasurementPlugin, is_system_plugin=True)
        self.csv_manifest = PluginRegistryService.register_plugin_class(CSVExportPlugin, is_system_plugin=True)

    def test_plugin_registration(self):
        self.assertEqual(PluginManifest.objects.count(), 3)
        self.assertEqual(self.py_manifest.plugin_id, "ecodep.runner.python")

    def test_plugin_dynamic_loader_and_execution(self):
        py_plugin = PluginLoaderService.load_plugin_by_id("ecodep.runner.python")
        result = py_plugin.execute_workload({'iterations': 20})
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertIn('elapsed_nanoseconds', result)

    def test_energy_plugin_execution(self):
        energy_plugin = PluginLoaderService.load_plugin_by_id("ecodep.sensor.energy")
        joules = energy_plugin.measure_energy_joules(duration_seconds=2.0)
        co2 = energy_plugin.estimate_co2_grams(energy_joules=joules)
        self.assertEqual(joules, 90.0)
        self.assertGreater(co2, 0.0)

    def test_csv_export_plugin(self):
        export_plugin = PluginLoaderService.load_plugin_by_id("ecodep.exporter.csv")
        dataset = [{'id': 1, 'name': 'test_pkg', 'score': 95.5}]
        payload = export_plugin.export_data(dataset)
        self.assertIn(b'test_pkg', payload)

    def test_event_bus_emission(self):
        event = PluginEventService.emit_event('BENCHMARK_COMPLETED', {'session_id': 101})
        self.assertEqual(event.event_type, 'BENCHMARK_COMPLETED')

    def test_plugin_registry_list_view(self):
        response = self.client.get(reverse('plugins:plugin_registry'))
        self.assertEqual(response.status_code, 200)
