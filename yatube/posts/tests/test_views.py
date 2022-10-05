from email.mime import image
from math import ceil

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post
from ..forms import PostForm


User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='auth'
        )
        cls.not_author = User.objects.create_user(
            username='not_author'
        )
        cls.group = Group.objects.create(
            title='test_title',
            description='test_description',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='test_post',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}))
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context['form'].instance.pk, self.post.id)
        self.assertTrue(response.context.get('is_edit'))

    def correct_context_for_pages(self, context):
        """Проверка контекста для главной страницы, групп и профайла."""
        post_object_fields = [
            (context.text, self.post.text),
            (context.author, self.user),
        ]
        for item, expected in post_object_fields:
            with self.subTest(item=item):
                self.assertEqual(item, expected)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': f'{self.group.slug}'}))
        )
        self.assertEqual(response.context.get('group').title, self.group.title)
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.correct_context_for_pages(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(response.context['author'], self.post.author)
        self.correct_context_for_pages(response.context['page_obj'][0])

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.correct_context_for_pages(response.context['page_obj'][0])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text = (
            (response.context['posts'].text, self.post.text),
            (response.context['posts'].group, self.group),
            (response.context['posts'].author, self.user),
        )
        for value, expected in post_text:
            self.assertEqual(value, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEST_POSTS = 25
        cls.user = User.objects.create_user(username='Stepan')
        cls.NUMBER_OF_PAGES = ceil(cls.TEST_POSTS / settings.COUNT_POST)
        cls.PAGE_COEF = 1
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        test_posts = []
        for number_of_posts in range(cls.TEST_POSTS):
            test_posts.append(Post(
                text=f'Текст поста № {number_of_posts}',
                group=cls.group,
                author=cls.user
            ))
        Post.objects.bulk_create(test_posts)

    def setUp(self):
        self.guest_client = Client()

    def test_paginator_post_in_page(self):
        pages_address = (
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': f'{self.group.slug}'}),
            reverse('posts:profile',
                    kwargs={'username': f'{self.user.username}'}),
        )
        for page in pages_address:
            with self.subTest(
                count_post_on__first_page=page
            ):
                first_page = len(
                    self.guest_client.get(page).context['page_obj']
                )
                last_page = len(
                    self.guest_client.get(
                        page + f'?page={self.NUMBER_OF_PAGES}'
                    ).context['page_obj']
                )
            self.assertEqual(
                first_page,
                settings.COUNT_POST,
            )
            self.assertEqual(
                last_page,
                self.TEST_POSTS - (
                    self.NUMBER_OF_PAGES - 1
                ) * settings.COUNT_POST
            )
