from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.not_author = User.objects.create_user(username='test_user2')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            text='тестовый текст',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        templates_url_names = [
            ('posts/index.html', reverse('posts:index')),
            (
                'posts/post_detail.html',
                reverse(
                    'posts:post_detail', kwargs={
                        'post_id': self.post.pk
                    }
                ),
            ),
            (
                'posts/group_list.html',
                reverse(
                    'posts:group_list', kwargs={
                        'slug': self.group.slug
                    }
                ),
            ),
            (
                'posts/profile.html',
                reverse(
                    'posts:profile', kwargs={
                        'username': 'test_user'
                    }
                ),
            ),
            (
                'posts/create_post.html',
                reverse(
                    'posts:post_create'
                ),
            ),
        ]
        for template, reverse_temp in templates_url_names:
            with self.subTest(address=template):
                response = self.authorized_client.get(reverse_temp)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_urls(self):
        address_names = [
            ('/', reverse('posts:index')),
            ('/create/', reverse('posts:post_create')),
            (
                f'/posts/{self.post.pk}/',
                reverse(
                    'posts:post_detail', kwargs={'post_id': self.post.pk}
                )
            ),
            (
                f'/group/{self.group.slug}/',
                reverse(
                    'posts:group_list', kwargs={'slug': self.group.slug}
                )
            ),
            (
                f'/profile/{self.user}/',
                reverse(
                    'posts:profile', kwargs={'username': 'test_user'}
                )
            ),
        ]
        for url, address in address_names:
            with self.subTest(address=address):
                self.assertEqual(url, address)

    def test_page(self):
        response = [
            (reverse('posts:index'), HTTPStatus.OK, False,),
            ('/unknow_page/', HTTPStatus.NOT_FOUND, False,),
            (
                reverse(
                    'posts:post_detail', kwargs={
                        'post_id': self.post.pk
                    }
                ), HTTPStatus.OK, False,
            ),
            (
                reverse(
                    'posts:group_list', kwargs={
                        'slug': self.group.slug
                    }
                ), HTTPStatus.OK, False,
            ),
            (
                reverse(
                    'posts:profile', kwargs={
                        'username': 'test_user'
                    }
                ), HTTPStatus.OK, False,
            ),
            (reverse(
                'posts:post_create'
            ), HTTPStatus.OK, True,),
            (
                reverse(
                    'posts:post_edit', kwargs={
                        'post_id': self.post.pk
                    }
                ), HTTPStatus.OK, True,
            ),
        ]
        for url, status, aut in response:
            with self.subTest(url=url):
                if aut:
                    response = self.authorized_client.get(url)
                else:
                    response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code, status
                )

    def test_url_redirect_anonymous_on_admin_login(self):
        respons = [
            (
                reverse('posts:post_create'),
                '/auth/login/?next=/create/'
            ),
            (
                reverse('posts:post_edit', kwargs={
                    'post_id': self.post.pk
                }),
                f'/auth/login/?next=/posts/{self.post.id}/edit/'
            )
        ]
        for url, address in respons:
            with self.subTest(address=address):
                respons = self.guest_client.get(url, follow=True)
                self.assertRedirects(respons, address)

    def test_urls_edit_page_authorized_user_but_not_author(self):
        self.authorized_client.force_login(self.not_author)
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            )
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            )
        )
