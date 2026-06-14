from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser

class UsersTestCase(TestCase):
    def setUp(self):
        self.client_user = CustomUser.objects.create_user(
            username='test_client',
            email='client@example.com',
            password='Password123!',
            telephone='+2250102030405',
            role=CustomUser.Role.CLIENT
        )
        self.agent_user = CustomUser.objects.create_user(
            username='test_agent',
            email='agent@example.com',
            password='Password123!',
            telephone='+2250202030405',
            role=CustomUser.Role.AGENT
        )
        self.admin_user = CustomUser.objects.create_superuser(
            username='test_admin',
            email='admin@example.com',
            password='Password123!',
            telephone='+2250302030405',
            role=CustomUser.Role.ADMIN
        )

    def test_user_roles(self):
        self.assertTrue(self.client_user.is_client)
        self.assertFalse(self.client_user.is_staff)
        self.assertTrue(self.admin_user.is_staff)

    def test_login_web_success(self):
        c = Client()
        response = c.post(reverse('login_web'), {
            'username': 'test_client',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home_web'))

    def test_login_web_failure(self):
        c = Client()
        response = c.post(reverse('login_web'), {
            'username': 'test_client',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_register_web_success(self):
        c = Client()
        response = c.post(reverse('register_web'), {
            'username': 'new_client',
            'email': 'new@example.com',
            'telephone': '+2250909090909',
            'password': 'NewPassword123!',
            'first_name': 'New',
            'last_name': 'Client',
            'region': 'Abidjan'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login_web'))
        self.assertTrue(CustomUser.objects.filter(username='new_client').exists())
