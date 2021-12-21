import shutil
import tempfile

from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from posts.models import Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HOME_URL = {
            'profile': reverse('posts:profile', args={'auth'}),
            'post_detail': reverse('posts:post_detail', args={1}),
            'post_create': reverse('posts:post_create'),
            'post_edit': reverse('posts:post_edit', args={1}),
        }
        cls.user = User.objects.create_user(username='auth')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создания поста создает запись в БД."""
        posts_count = Post.objects.count()
        picture_content = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='picture.gif',
            content=picture_content,
            content_type='image/gif'
        )
        response = self.authorized_client.post(
            self.HOME_URL['post_create'],
            {'text': 'Пост с картинкой', 'image': uploaded}
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Пост с картинкой',
                image='posts/picture.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирования поста меняет запись в БД."""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            self.HOME_URL['post_edit'],
            {'text': 'Тестовый текст изменен'}
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст изменен'
            ).exists()
        )
