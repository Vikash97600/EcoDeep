from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.users.models import Role, RoleChoices, UserProfile

class DashboardWorkspacesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role = Role.objects.create(role_name=RoleChoices.ADMIN)
        self.researcher_role = Role.objects.create(role_name=RoleChoices.RESEARCHER)
        self.dev_role = Role.objects.create(role_name=RoleChoices.DEVELOPER)

        self.admin_user = User.objects.create_superuser(username='adminusr', email='admin@ecodep.local', password='AdminPass123!')
        profile, _ = UserProfile.objects.get_or_create(user=self.admin_user)
        profile.role = self.admin_role
        profile.save()

    def test_admin_workspace_view(self):
        self.client.login(username='adminusr', password='AdminPass123!')
        response = self.client.get(reverse('dashboard:admin_workspace'))
        self.assertEqual(response.status_code, 200)

    def test_analytics_dashboard_view(self):
        response = self.client.get(reverse('dashboard:analytics_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_comparison_studio_view(self):
        response = self.client.get(reverse('dashboard:comparison_studio'))
        self.assertEqual(response.status_code, 200)
