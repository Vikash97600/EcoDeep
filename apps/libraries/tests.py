from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.libraries.models import ProgrammingLanguage, Category, Library, SimilarLibraryMapping
from apps.libraries.services import BulkDataService
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
            "Library Name,Official Name,Language,Category,Version,License,Description\n"
            "msgpack,MessagePack Python,Python,Data Serialization,1.0.7,Apache-2.0,Fast binary serialization\n"
            "cbor2,CBOR2 Python,Python,Data Serialization,5.5.1,MIT,CBOR decoder library\n"
        ).encode('utf-8')

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

