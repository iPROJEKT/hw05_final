from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class ViewTestClass(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')

    def setUp(self):
        self.authorized_client = Client()

    def test_page_404_unexists_at_desired_location(self):
        response = self.authorized_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
