from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.conf import settings

from ..models import Post, User, Group, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
            'text': 'Тескст поста',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
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
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(self.uploaded, form_data['image'])

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
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём фикстуру с необходимыми данными."""
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post_id=cls.post.id,
            author=cls.user,
            text='Тестовый коммент'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Проверка создания комментария"""
        comment_list_before = set(Comment.objects.values_list(
            'id', flat=True
        ))
        form_data = {
            'post_id': self.post.id,
            'text': 'Тестовый коммент да',
        }
        comment_list = set(Post.objects.values_list(
            'id', flat=True
        ))
        comment_len = comment_list - comment_list_before
        self.assertEqual(
            len(comment_len), 1
        )
        comments_now = Post.objects.get(id=list(comment_len)[0])
        comment = comments_now[0]
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post_id, form_data['post_id'])

    def test_no_edit_comment(self):
        """Проверка запрета комментирования не авторизованого пользователя"""
        comment_list_before = set(Comment.objects.values_list(
            'id', flat=True
        ))
        form_data = {'text': 'Тестовый коммент2'}
        comment_list = set(Post.objects.values_list(
            'id', flat=True
        ))
        comment_len = comment_list - comment_list_before
        self.assertEqual(
            len(comment_len), 1
        )