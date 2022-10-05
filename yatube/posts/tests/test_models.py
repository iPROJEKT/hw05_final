from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Group, Post


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        field_verboses = [
            ('author', 'Автор'),
            ('group', 'Группа'),
        ]
        for field, expected_value in field_verboses:
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(
                        field
                    ).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        field_help_texts = [
            ('text', 'text'),
            ('group', 'Группа')
        ]
        for name, field in field_help_texts:
            with self.subTest(field=name):
                self.assertEqual(
                    self.post._meta.get_field(
                        name
                    ).verbose_name,
                    field
                )

    def test_object_name_is_title_fild(self):
        self.assertEqual(
            self.post.text[:Post.FIRST_TEXT], str(self.post)
        )
