from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkStatusChoices,
    BenchmarkTask,
)
from apps.libraries.models import Category, Library, LibraryVersion, ProgrammingLanguage
from apps.users.models import Role, RoleChoices, UserProfile


class APIGatewayTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_role = Role.objects.create(role_name=RoleChoices.ADMIN)
        self.user = User.objects.create_user(username='apiuser', email='api@ecodep.local', password='APIPassword123!')
        
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.role = self.admin_role
        self.profile.save()

        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

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

    def test_health_check_endpoint(self):
        response = self.client.get(reverse('api:api_health'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'HEALTHY')

    def test_metrics_endpoint(self):
        response = self.client.get(reverse('api:api_metrics'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_libraries', response.data)

    def test_library_list_api(self):
        response = self.client.get(reverse('api:library-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_recommendation_query_api(self):
        session = BenchmarkSession.objects.create(session_name="API Session", status=BenchmarkStatusChoices.COMPLETED)
        BenchmarkResult.objects.create(
            session=session, library_version=self.ver1, task=self.task, dataset=self.dataset, execution_time=100.0, average_cpu=15.0, peak_memory=50.0, energy=20.0, co2=0.005, green_score=62.10
        )
        BenchmarkResult.objects.create(
            session=session, library_version=self.ver2, task=self.task, dataset=self.dataset, execution_time=25.0, average_cpu=10.0, peak_memory=20.0, energy=5.0, co2=0.001, green_score=93.40
        )

        response = self.client.post(reverse('api:recommendation-query'), {
            'target_library_id': self.lib1.id,
            'task_id': self.task.id,
            'profile_type': 'BEST_OVERALL'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 2)
