import time
import tracemalloc
import psutil
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.benchmark.models import BenchmarkSession, BenchmarkTask, BenchmarkDataset, BenchmarkJob, BenchmarkResult, RawExecutionSample, BenchmarkStatusChoices, WorkerNode, JobRetryLog
from apps.libraries.models import ProgrammingLanguage, Category, Library, LibraryVersion
from apps.users.models import Role, RoleChoices, UserProfile
from apps.benchmark.services.statistics_service import StatisticalAnalysisService
from apps.benchmark.services.validation_service import ValidationService
from apps.benchmark.services.repository_service import RepositoryService
from apps.benchmark.services.comparison_service import ComparisonService
from apps.benchmark.services.export_service import ExportService
from apps.benchmark.services.orchestrator.queue_service import QueueService
from apps.benchmark.services.orchestrator.worker_service import WorkerService
from apps.benchmark.services.orchestrator.resource_monitor_service import ResourceMonitorService
from apps.benchmark.services.orchestrator.retry_service import RetryService
from apps.benchmark.services.orchestrator.scheduler_service import SchedulerService

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
        is_safe, cpu_pct, ram_pct = ResourceMonitorService.is_host_resource_available()
        self.assertIsInstance(is_safe, bool)

    def test_exponential_backoff_retry(self):
        requeued, msg = RetryService.handle_job_failure(self.job1, Exception("Transient connection timeout"))
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
        self.assertTrue(BenchmarkSession.objects.filter(session_name='Live Integration Run').exists())

