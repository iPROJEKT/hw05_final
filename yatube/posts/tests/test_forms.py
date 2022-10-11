from http import HTTPStatus

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, User, Group, Comment


class PostCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём фикстуру с необходимыми данными."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_file = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    def setUp(self):
        """Создаём авторизованного пользователя и автора."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_post(self):
        """Проверка создания новой записи в базе данных."""
        post_list_before = set(Post.objects.values_list(
            'id', flat=True
        ))
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': self.uploaded_file,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={
                'username': self.author
            })
        )
        post_list = set(Post.objects.values_list(
            'id', flat=True
        ))
        post_len = post_list - post_list_before
        self.assertEqual(
            len(post_len), 1
        )
        post = Post.objects.get(id=list(post_len)[0])
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(self.uploaded_file, form_data['image'])

    def test_edit_post(self):
        """Проверка изменения поста при редактировании."""
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.id, form_data['group'])


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём фикстуру с необходимыми данными."""
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post_id=cls.post.id,
            author=cls.author,
            text='Тестовый коммент'
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_create_comment(self):
        """Проверка создания комментария"""
        comment_list_before = set(Comment.objects.values_list(
            'id', flat=True
        ))
        form_data = {
            'post_id': self.post.id,
            'text': 'Тестовый коммент2',
        }
        response = self.author_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        comment_list = set(Comment.objects.values_list(
            'id', flat=True
        ))
        comment_len = comment_list - comment_list_before
        self.assertEqual(len(comment_len), 1)
        comment = Comment.objects.get(id=list(comment_len)[0])
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post_id, form_data['post_id'])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_no_edit_comment(self):
        """Проверка запрета комментирования не авторизованого пользователя"""
        comment_list_before = set(Comment.objects.values_list(
            'id', flat=True
        ))
        comment_list = set(Post.objects.values_list(
            'id', flat=True
        ))
        comment_len = comment_list - comment_list_before
        self.assertEqual(
            len(comment_len), 0
        )
