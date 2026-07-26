from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.users.models import Role, RoleChoices, UserProfile

class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_role = Role.objects.create(role_name=RoleChoices.ADMIN, description="Admin")
        self.dev_role = Role.objects.create(role_name=RoleChoices.DEVELOPER, description="Dev")
        self.user = User.objects.create_user(username='testdev', email='dev@ecodep.local', password='SecurePass123!')
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.role = self.dev_role
        self.profile.save()

    def test_login_successful(self):
        response = self.client.post(reverse('authentication:login'), {
            'username': 'testdev',
            'password': 'SecurePass123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_invalid_password_fails(self):
        response = self.client.post(reverse('authentication:login'), {
            'username': 'testdev',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_registration_flow(self):
        response = self.client.post(reverse('authentication:register'), {
            'first_name': 'New',
            'last_name': 'User',
            'username': 'newuser',
            'email': 'new@ecodep.local',
            'password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!',
            'role': self.dev_role.id,
            'institution': 'MCA College',
            'department': 'CS',
            'agree_terms': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
