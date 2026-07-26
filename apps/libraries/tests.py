from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.libraries.models import ProgrammingLanguage, Category, Library, SimilarLibraryMapping
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
