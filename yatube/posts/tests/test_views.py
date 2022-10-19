from math import ceil

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings

from ..forms import PostForm
from ..models import Post, Group, User, Comment, Follow


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
        cls.small_gif = (
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
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
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post_id=cls.post.id,
            author=cls.user,
            text='Тестовый коммент',
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
        Follow.objects.create(
            user=self.user,
            author=self.post.author)
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.post.author}))
        self.assertEqual(response.context['author'], self.post.author)
        self.correct_context_for_pages(response.context['page_obj'][0])
        self.assertEqual(response.context['following'], True)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.correct_context_for_pages(response.context['page_obj'][0])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_text = (
            (response.context['post'].text, self.post.text),
            (response.context['post'].group, self.group),
            (response.context['post'].author, self.user),
        )
        for value, expected in post_text:
            self.assertEqual(value, expected)

    def test_cache_context(self):
        """Проверка кэширования страницы index"""
        before_create_post = self.authorized_client.get(
            reverse('posts:index'))
        first_item_before = before_create_post.content
        Post.objects.create(
            author=self.user,
            text='Проверка кэша',
            group=self.group)
        after_create_post = self.authorized_client.get(reverse('posts:index'))
        first_item_after = after_create_post.content
        self.assertEqual(first_item_after, first_item_before)
        cache.clear()
        after_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_item_after, after_clear)


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


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Текстовый текст',
            author=cls.author
        )
        cls.user = User.objects.create_user(username='user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_follower_see_new_post(self):
        """Новая запись пользователя появляется в ленте тех,
         кто на него подписан"""
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_post = response.context['page_obj'].object_list[0]
        self.assertEqual(self.post, new_post)

    def test_follow_another_user(self):
        """Авторизованный пользователь,
        может подписываться на других пользователей."""
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.author
        ).exists())
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author}
        ))
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.author
        ).exists())

    def test_unfollow(self):
        """Авторизованный пользователь,
        может отписываться от других пользователей."""
        Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author}
        ))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            )
        )

    def test_no_view_post_for_not_follower(self):
        """Пост не появляется в ленте подписок,
         если нет подписки на автора."""
        self.authorized_client.force_login(self.author)
        new_post_follower = Post.objects.create(
            author=self.author,
            text='Текстовый текст')
        Follow.objects.create(
            user=self.author,
            author=self.user
        )
        response_unfollower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_post_unfollower = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_follower, new_post_unfollower)
