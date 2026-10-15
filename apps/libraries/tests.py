from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from apps.libraries.models import (
    Category,
    Library,
    ProgrammingLanguage,
    SimilarLibraryMapping,
)
from apps.users.models import Role, RoleChoices, UserProfile


class LibraryManagementTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role = Role.objects.create(role_name=RoleChoices.ADMIN)
        self.admin_user = User.objects.create_superuser(username='adminuser', email='admin@ecodep.local', password='AdminPass123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.admin_user)
        profile.role = self.admin_role
        profile.save()

        self.lang = ProgrammingLanguage.objects.create(language_name="Python", slug="python")
        self.cat = Category.objects.create(category_name="Data Serialization", slug="data-serialization", description="JSON serializers")

        self.lib_json = Library.objects.create(
            library_name="json", official_name="Python Standard JSON",
            programming_language=self.lang, category=self.cat,
            description="Standard json library", current_version="3.11.4"
        )
        self.lib_orjson = Library.objects.create(
            library_name="orjson", official_name="orjson Fast JSON",
            programming_language=self.lang, category=self.cat,
            description="Fast Rust-based JSON library", current_version="3.9.1"
        )

    def test_library_creation(self):
        self.assertEqual(Library.objects.count(), 2)
        self.assertEqual(str(self.lib_json), "json (Python)")

    def test_similar_library_mapping(self):
        mapping = SimilarLibraryMapping.objects.create(
            source_library=self.lib_json,
            target_library=self.lib_orjson,
            similarity_type="DIRECT",
            similarity_score=0.95,
            reason="Both serialize and deserialize JSON objects"
        )
        self.assertEqual(SimilarLibraryMapping.objects.count(), 1)
        self.assertEqual(str(mapping), "json <-> orjson (0.95)")

    def test_library_list_view(self):
        response = self.client.get(reverse('libraries:library_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "orjson")

    def test_manual_library_registration(self):
        self.client.login(username='adminuser', password='AdminPass123!')
        post_data = {
            'library_name': 'ujson',
            'official_name': 'UltraJSON Python Library',
            'programming_language': self.lang.id,
            'category': self.cat.id,
            'description': 'Fast UltraJSON package',
            'current_version': '5.8.0',
            'license': 'BSD-3-Clause',
            'package_manager': 'PyPI'
        }
        res = self.client.post(reverse('libraries:library_create'), data=post_data)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Library.objects.filter(library_name='ujson').exists())

    def test_bulk_csv_import_and_export(self):
        self.client.login(username='adminuser', password='AdminPass123!')
        
        # Test CSV export
        exp_res = self.client.get(reverse('libraries:export_data', kwargs={'format_type': 'csv'}))
        self.assertEqual(exp_res.status_code, 200)
        self.assertIn("orjson", exp_res.content.decode('utf-8'))

        # Test CSV import
        csv_content = (
            b"Library Name,Official Name,Language,Category,Version,License,Description\n"
            b"msgpack,MessagePack Python,Python,Data Serialization,1.0.7,Apache-2.0,Fast binary serialization\n"
            b"cbor2,CBOR2 Python,Python,Data Serialization,5.5.1,MIT,CBOR decoder library\n"
        )

        uploaded_file = SimpleUploadedFile("libraries.csv", csv_content, content_type="text/csv")
        imp_res = self.client.post(reverse('libraries:bulk_import'), {'file': uploaded_file})
        self.assertEqual(imp_res.status_code, 302)

        self.assertTrue(Library.objects.filter(library_name='msgpack').exists())
        self.assertTrue(Library.objects.filter(library_name='cbor2').exists())

    def test_mapping_creation_view(self):
        self.client.login(username='adminuser', password='AdminPass123!')
        post_data = {
            'source_library': self.lib_json.id,
            'target_library': self.lib_orjson.id,
            'similarity_type': 'DIRECT',
            'similarity_score': '0.92',
            'reason': 'Direct replacement JSON serializer'
        }
        res = self.client.post(reverse('libraries:mapping_create'), data=post_data)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(SimilarLibraryMapping.objects.filter(source_library=self.lib_json, target_library=self.lib_orjson).exists())


from apps.benchmark.models import (
    BenchmarkDataset,
    BenchmarkJob,
    BenchmarkResult,
    BenchmarkSession,
    BenchmarkStatusChoices,
    BenchmarkTask,
)
from apps.libraries.models import LibraryVersion
from apps.libraries.services import CategoryPurgeService


class CategoryPurgeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role = Role.objects.create(role_name=RoleChoices.ADMIN)
        self.admin_user = User.objects.create_superuser(username='purgeadmin', email='purgeadmin@ecodep.local', password='PurgePass123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.admin_user)
        profile.role = self.admin_role
        profile.save()

        self.lang = ProgrammingLanguage.objects.create(language_name="Python", slug="python-purge")

        # Category to be purged
        self.cat_target = Category.objects.create(category_name="Data Serialization Target", slug="data-ser-target")
        self.lib1 = Library.objects.create(library_name="target_lib_1", programming_language=self.lang, category=self.cat_target)
        self.ver1 = LibraryVersion.objects.create(library=self.lib1, version_number="1.0.0")
        self.lib2 = Library.objects.create(library_name="target_lib_2", programming_language=self.lang, category=self.cat_target)
        self.ver2 = LibraryVersion.objects.create(library=self.lib2, version_number="2.0.0")

        self.dataset_target = BenchmarkDataset.objects.create(
            dataset_name="Target Dataset 1", dataset_category=self.cat_target, dataset_type="JSON"
        )
        self.task_target = BenchmarkTask.objects.create(
            task_name="Target Workload Task", category=self.cat_target, dataset=self.dataset_target
        )
        self.session_target = BenchmarkSession.objects.create(
            session_name="Target Benchmark Session", status=BenchmarkStatusChoices.COMPLETED
        )
        self.job1 = BenchmarkJob.objects.create(
            session=self.session_target, library_version=self.ver1, task=self.task_target, status=BenchmarkStatusChoices.COMPLETED
        )
        self.res1 = BenchmarkResult.objects.create(
            session=self.session_target, library_version=self.ver1, task=self.task_target, dataset=self.dataset_target,
            execution_time=12.5, energy=1.5, co2=0.0002, green_score=85.0
        )

        # Unrelated category (must NOT be touched)
        self.cat_other = Category.objects.create(category_name="HTTP Networking Other", slug="http-other")
        self.lib_other = Library.objects.create(library_name="other_lib_1", programming_language=self.lang, category=self.cat_other)
        self.ver_other = LibraryVersion.objects.create(library=self.lib_other, version_number="1.0.0")
        self.dataset_other = BenchmarkDataset.objects.create(
            dataset_name="Other Dataset", dataset_category=self.cat_other, dataset_type="JSON"
        )
        self.task_other = BenchmarkTask.objects.create(
            task_name="Other Task", category=self.cat_other, dataset=self.dataset_other
        )
        self.session_other = BenchmarkSession.objects.create(
            session_name="Other Benchmark Session", status=BenchmarkStatusChoices.COMPLETED
        )
        self.job_other = BenchmarkJob.objects.create(
            session=self.session_other, library_version=self.ver_other, task=self.task_other, status=BenchmarkStatusChoices.COMPLETED
        )

    def test_category_purge_preview(self):
        preview = CategoryPurgeService.get_category_purge_preview(self.cat_target)
        self.assertEqual(preview['libraries_count'], 2)
        self.assertIn("target_lib_1", preview['libraries'])
        self.assertIn("target_lib_2", preview['libraries'])
        self.assertEqual(preview['sessions_count'], 1)
        self.assertEqual(preview['tasks_count'], 1)
        self.assertEqual(preview['datasets_count'], 1)
        self.assertEqual(preview['results_count'], 1)

    def test_purge_category_data_keep_category(self):
        result = CategoryPurgeService.purge_category_data(
            category=self.cat_target, delete_category=False, user=self.admin_user
        )
        self.assertEqual(result['libraries_deleted'], 2)
        self.assertEqual(result['sessions_deleted'], 1)
        self.assertEqual(result['tasks_deleted'], 1)
        self.assertEqual(result['datasets_deleted'], 1)
        self.assertFalse(result['category_deleted'])

        # Verify target resources were deleted
        self.assertFalse(Library.objects.filter(category=self.cat_target).exists())
        self.assertFalse(BenchmarkSession.objects.filter(id=self.session_target.id).exists())
        self.assertFalse(BenchmarkTask.objects.filter(category=self.cat_target).exists())
        self.assertFalse(BenchmarkDataset.objects.filter(dataset_category=self.cat_target).exists())
        self.assertFalse(BenchmarkResult.objects.filter(id=self.res1.id).exists())

        # Verify category itself still exists
        self.assertTrue(Category.objects.filter(id=self.cat_target.id).exists())

        # Verify UNRELATED category resources were NOT deleted
        self.assertTrue(Library.objects.filter(id=self.lib_other.id).exists())
        self.assertTrue(BenchmarkSession.objects.filter(id=self.session_other.id).exists())
        self.assertTrue(BenchmarkTask.objects.filter(id=self.task_other.id).exists())
        self.assertTrue(BenchmarkDataset.objects.filter(id=self.dataset_other.id).exists())

    def test_purge_category_data_with_category_deleted(self):
        result = CategoryPurgeService.purge_category_data(
            category=self.cat_target, delete_category=True, user=self.admin_user
        )
        self.assertTrue(result['category_deleted'])
        self.assertFalse(Category.objects.filter(id=self.cat_target.id).exists())
        self.assertFalse(Library.objects.filter(library_name="target_lib_1").exists())

    def test_category_data_delete_views_and_api(self):
        self.client.login(username='purgeadmin', password='PurgePass123!')

        # Test GET confirmation page
        response = self.client.get(reverse('libraries:category_data_delete'), {'category': self.cat_target.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Target Workload Task")
        self.assertContains(response, "target_lib_1")

        # Test API summary endpoint
        api_res = self.client.get(reverse('libraries:api_category_summary', kwargs={'category_id': self.cat_target.id}))
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['libraries_count'], 2)
        self.assertEqual(data['data']['sessions_count'], 1)

        # Test POST deletion
        post_res = self.client.post(reverse('libraries:category_data_delete'), {
            'category': self.cat_target.id,
            'delete_category': 'on'
        })
        self.assertEqual(post_res.status_code, 302)
        self.assertFalse(Library.objects.filter(category=self.cat_target).exists())
        self.assertFalse(Category.objects.filter(id=self.cat_target.id).exists())


