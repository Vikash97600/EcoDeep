from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkJob,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkStatusChoices,
    BenchmarkTask,
    JobRetryLog,
    WorkerNode,
)
from apps.benchmark.services.comparison_service import ComparisonService
from apps.benchmark.services.export_service import ExportService
from apps.benchmark.services.orchestrator.queue_service import QueueService
from apps.benchmark.services.orchestrator.resource_monitor_service import (
    ResourceMonitorService,
)
from apps.benchmark.services.orchestrator.retry_service import RetryService
from apps.benchmark.services.orchestrator.worker_service import WorkerService
from apps.benchmark.services.repository_service import RepositoryService
from apps.benchmark.services.validation_service import ValidationService
from apps.libraries.models import Category, Library, LibraryVersion, ProgrammingLanguage
from apps.users.models import Role, RoleChoices, UserProfile


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
        orjson_comp = comp['comparisons'][1]
        self.assertEqual(orjson_comp['time_delta_pct'], -75.0)

    def test_repository_csv_export(self):
        response = ExportService.export_repository_csv(BenchmarkResult.objects.all())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')


class OrchestratorFrameworkTestCase(TestCase):
    def setUp(self):
        self.lang = ProgrammingLanguage.objects.create(language_name="Python", slug="python")
        self.cat = Category.objects.create(category_name="Data Serialization", slug="data-serialization", description="JSON parsers")

        self.dataset = BenchmarkDataset.objects.create(
            dataset_name="10MB JSON Payload", dataset_category=self.cat, dataset_size_bytes=10485760, description="Test dataset"
        )
        self.task = BenchmarkTask.objects.create(
            task_name="JSON Deserialization 10MB", category=self.cat, dataset=self.dataset, description="Workload task", iterations=10
        )
        self.lib = Library.objects.create(library_name="json", official_name="Python stdlib json", programming_language=self.lang, category=self.cat, description="Stdlib JSON")
        self.ver = LibraryVersion.objects.create(library=self.lib, version_number="3.11.4")

        self.session = BenchmarkSession.objects.create(session_name="Orchestrator Session", status=BenchmarkStatusChoices.PENDING)
        self.job1 = BenchmarkJob.objects.create(session=self.session, library_version=self.ver, task=self.task, priority=1, status=BenchmarkStatusChoices.PENDING)
        self.job2 = BenchmarkJob.objects.create(session=self.session, library_version=self.ver, task=self.task, priority=5, status=BenchmarkStatusChoices.PENDING)

    def test_priority_queue_ordering(self):
        next_job = QueueService.get_next_job()
        self.assertEqual(next_job, self.job2)  # Higher priority (5 vs 1)

    def test_worker_node_registration(self):
        worker = WorkerService.register_current_node()
        self.assertIsNotNone(worker)
        self.assertTrue(WorkerNode.objects.filter(hostname=worker.hostname).exists())

    def test_resource_monitor_guard(self):
        is_safe, _cpu_pct, _ram_pct = ResourceMonitorService.is_host_resource_available()
        self.assertIsInstance(is_safe, bool)

    def test_exponential_backoff_retry(self):
        requeued, _msg = RetryService.handle_job_failure(self.job1, Exception("Transient connection timeout"))
        self.assertTrue(requeued)
        self.assertEqual(self.job1.retry_count, 1)
        self.assertEqual(JobRetryLog.objects.count(), 1)

    def test_task_creation_and_session_views(self):
        client = Client()
        admin_role = Role.objects.create(role_name=RoleChoices.ADMIN)
        admin_user = User.objects.create_superuser(username='benchadmin', email='benchadmin@ecodep.local', password='AdminPass123!')
        profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        profile.role = admin_role
        profile.save()
        client.login(username='benchadmin', password='AdminPass123!')

        # Test creating a benchmark task
        task_data = {
            'task_name': 'New Dynamic Workload Task',
            'category': self.cat.id,
            'iterations': 20,
            'warmup_runs': 3,
            'timeout_seconds': 15,
            'description': 'Dynamic workload testing'
        }
        res_task = client.post(reverse('benchmark:task_create'), data=task_data)
        self.assertEqual(res_task.status_code, 302)
        created_task = BenchmarkTask.objects.filter(task_name='New Dynamic Workload Task').first()
        self.assertIsNotNone(created_task)

        # Test creating a benchmark session with the newly created task
        session_data = {
            'session_name': 'Live Integration Run',
            'category': self.cat.id,
            'task': created_task.id,
            'library_versions': [self.ver.id],
            'notes': 'Automated session integration'
        }
        res_sess = client.post(reverse('benchmark:session_create'), data=session_data)
        self.assertEqual(res_sess.status_code, 302)
        sess = BenchmarkSession.objects.filter(session_name='Live Integration Run').first()
        self.assertIsNotNone(sess)

        # Trigger benchmark runner execution
        res_trigger = client.post(reverse('benchmark:trigger_runner', kwargs={'session_id': sess.id}))
        self.assertEqual(res_trigger.status_code, 302)

        # Verify all enqueued jobs are completed and NOT failed
        sess.refresh_from_db()
        self.assertEqual(sess.status, BenchmarkStatusChoices.COMPLETED)
        self.assertEqual(sess.jobs.filter(status=BenchmarkStatusChoices.COMPLETED).count(), 1)
        self.assertEqual(sess.jobs.filter(status=BenchmarkStatusChoices.FAILED).count(), 0)

        # Verify physical telemetry and green score results are recorded
        result = BenchmarkResult.objects.filter(session=sess).first()
        self.assertIsNotNone(result)
        self.assertGreater(result.execution_time, 0.0)
        self.assertGreater(result.cpu_usage, 0.0)
        self.assertGreater(result.peak_memory, 0.0)
        self.assertGreater(result.energy, 0.0)
        self.assertGreater(result.green_score, 0.0)
        self.assertGreater(result.raw_samples.count(), 0)


from apps.benchmark.services.dataset_generator import DeterministicDatasetGenerator


class DatasetGeneratorTestCase(TestCase):
    def setUp(self):
        self.cat_json = Category.objects.create(category_name="JSON Serialization", slug="json-ser")
        self.cat_http = Category.objects.create(category_name="HTTP Client Requests", slug="http-req")
        self.lang = ProgrammingLanguage.objects.create(language_name="Python", slug="py-gen")
        self.lib_orjson = Library.objects.create(library_name="orjson", programming_language=self.lang, category=self.cat_json)

    def test_unique_dataset_generation_per_category(self):
        """Verify that generating datasets for different categories produces unique, domain-tailored content."""
        ds_json = DeterministicDatasetGenerator.generate_dataset(
            dataset_type='JSON', record_count=10, seed=42, category_name="JSON Serialization", library_name="orjson", dataset_name="Payload A"
        )
        ds_http = DeterministicDatasetGenerator.generate_dataset(
            dataset_type='JSON', record_count=10, seed=42, category_name="HTTP Client Requests", library_name="requests", dataset_name="Payload B"
        )

        self.assertNotEqual(ds_json, ds_http, "Datasets for different categories should not be identical.")
        self.assertIn("transaction_id", ds_json)
        self.assertIn("request_id", ds_http)

    def test_unique_dataset_generation_per_dataset_name(self):
        """Verify that different dataset names for the same seed produce distinct datasets."""
        ds1 = DeterministicDatasetGenerator.generate_dataset(
            dataset_type='CSV', record_count=10, seed=42, category_name="JSON Serialization", dataset_name="Small Payload"
        )
        ds2 = DeterministicDatasetGenerator.generate_dataset(
            dataset_type='CSV', record_count=10, seed=42, category_name="JSON Serialization", dataset_name="Large Payload"
        )

        self.assertNotEqual(ds1, ds2, "Different dataset names must produce distinct datasets.")

    def test_xml_and_txt_format_generation(self):
        """Verify XML and TXT format generation."""
        xml_content = DeterministicDatasetGenerator.generate_dataset(
            dataset_type='XML', record_count=5, seed=42, category_name="XML Processing", dataset_name="XML Test"
        )
        txt_content = DeterministicDatasetGenerator.generate_dataset(
            dataset_type='TXT', record_count=5, seed=42, category_name="Plain Text", dataset_name="TXT Test"
        )

        self.assertIn("<dataset", xml_content)
        self.assertIn("<record>", xml_content)
        self.assertIn("# Synthetic Text Payload", txt_content)



