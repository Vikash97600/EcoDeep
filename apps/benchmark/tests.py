from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.benchmark.models import BenchmarkSession, BenchmarkTask, BenchmarkDataset, BenchmarkJob, BenchmarkStatusChoices
from apps.libraries.models import ProgrammingLanguage, Category, Library, LibraryVersion
from apps.users.models import Role, RoleChoices, UserProfile
from apps.benchmark.services.session_service import SessionService
from apps.benchmark.services.environment_service import EnvironmentService

class BenchmarkEngineTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role = Role.objects.create(role_name=RoleChoices.ADMIN)
        self.admin_user = User.objects.create_superuser(username='benchadmin', email='admin@ecodep.local', password='AdminPass123!')
        UserProfile.objects.create(user=self.admin_user, role=self.admin_role)

        self.lang = ProgrammingLanguage.objects.create(language_name="Python", slug="python")
        self.cat = Category.objects.create(category_name="Data Serialization", slug="data-serialization", description="JSON serializers")

        self.dataset = BenchmarkDataset.objects.create(
            dataset_name="10MB Synthetic JSON", dataset_category=self.cat, dataset_size_bytes=10485760, description="Test dataset"
        )
        self.task = BenchmarkTask.objects.create(
            task_name="JSON Deserialization 10MB", category=self.cat, dataset=self.dataset, description="Workload task", iterations=50
        )

        self.lib = Library.objects.create(
            library_name="orjson", official_name="orjson Fast JSON", programming_language=self.lang, category=self.cat, description="Fast JSON"
        )
        self.ver = LibraryVersion.objects.create(library=self.lib, version_number="3.9.1")

    def test_environment_validation(self):
        is_valid, details = EnvironmentService.validate_environment()
        self.assertTrue(isinstance(is_valid, bool))
        self.assertIn("Host CPU Utilization", details)

    def test_session_creation_service(self):
        session = SessionService.create_session(
            session_name="JSON Benchmark Run",
            admin_user=self.admin_user,
            task=self.task,
            library_versions=[self.ver],
            notes="Testing session creation service"
        )
        self.assertEqual(BenchmarkSession.objects.count(), 1)
        self.assertEqual(BenchmarkJob.objects.count(), 1)
        self.assertEqual(session.status, BenchmarkStatusChoices.PENDING)

    def test_session_list_view(self):
        response = self.client.get(reverse('benchmark:session_list'))
        self.assertEqual(response.status_code, 200)
