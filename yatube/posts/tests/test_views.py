from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, User, Comment, Follow


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.HOME_URL = {
            'index': reverse('posts:index'),
            'group': reverse('posts:group_list', args={'test'}),
            'profile': reverse('posts:profile', args={'auth'}),
            'post_detail': reverse('posts:post_detail', args={1}),
            'post_create': reverse('posts:post_create'),
            'post_edit': reverse('posts:post_edit', args={1}),
            'tech': reverse('about:tech'),
            'author': reverse('about:author'),
            'follow': reverse('posts:profile_follow', args={'auth'}),
            'unfollow': reverse('posts:profile_unfollow', args={'auth'}),
            'follow_index': reverse('posts:follow_index'),
        }
        cls.user = User.objects.create_user(username='auth')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.follower = User.objects.create_user(username='follower')
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower)
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'about/tech.html': 'tech',
            'posts/index.html': 'index',
            'about/author.html': 'author',
            'posts/profile.html': 'profile',
            'posts/group_list.html': 'group',
            'posts/create_post.html': 'post_create',
            'posts/post_detail.html': 'post_detail',
        }
        for template, url_label in templates_pages_names.items():
            with self.subTest(field=url_label):
                response = self.auth_client.get(self.HOME_URL[url_label])
                self.assertTemplateUsed(response, template)

    def test_extra_check_when_creating_post(self):
        """Корректно выводит количество постов на страницу."""
        pages_for_test = ('index', 'group', 'profile')
        len_obj = Post.objects.count()
        for url_label in pages_for_test:
            with self.subTest(field=url_label):
                response = self.auth_client.get(self.HOME_URL[url_label])
                self.assertEqual(len(response.context['page_obj']), len_obj)

    def test_post_in_main_and_group_and_profile_page(self):
        """Пост есть на главной странице, страинцы группы и в профиле."""
        pages_for_test = ('index', 'group', 'profile')
        for url_label in pages_for_test:
            with self.subTest(field=url_label):
                response = self.guest_client.get(self.HOME_URL[url_label])
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object, self.post)

    def test_new_post_not_in_wrong_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        new_group = Group.objects.create(
            title='Вторая группа',
            slug='second',
            description='Описание второй группы',
        )
        response = self.auth_client.get(
            reverse('posts:group_list', args={'second'})
        )
        self.assertNotIn(self.post, response.context['page_obj'])
        first_post_in_new_group = Post.objects.filter(group=new_group).first()
        self.assertNotEqual(first_post_in_new_group, self.post)
        first_post_without_group = Post.objects.filter(group=None).first()
        self.assertNotEqual(first_post_without_group, self.post)

    def test_context_on_pages(self):
        """
        Проверка контекста шаблонов главной страницы,
        страницы группы, профиля и поста
        """
        pages_for_test = ('index', 'group', 'profile', 'post_detail')
        for url_label in pages_for_test:
            with self.subTest(field=url_label):
                response = self.auth_client.get(self.HOME_URL[url_label])
                first_object = (response.context.get('post')
                                or response.context['page_obj'][0])
                self.assertEqual(first_object.text, self.post.text)
                self.assertEqual(first_object.author, self.user)
                self.assertEqual(first_object.group, self.post.group)
                self.assertEqual(first_object.image, self.post.image)

    def test_form_show_correct_context(self):
        """Проверка контекста создания и редактирования поста."""
        pages_for_test = ('post_create', 'post_edit')
        for url_label in pages_for_test:
            response = self.auth_client.get(self.HOME_URL[url_label])
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField,
            }
            for field, expected in form_fields.items():
                with self.subTest(field=field):
                    form_field = response.context['form'].fields[field]
                    self.assertIsInstance(form_field, expected)

    def test_comment_is_on_correct_page(self):
        '''Комментарий появляется только на странице конкретного поста'''
        new_post = Post.objects.create(
            author=self.user,
            text='Тест для комментаря',
            pk=5
        )
        test_comment = Comment.objects.create(
            text='Тестовый комментарий',
            post=new_post,
            author=self.user,
        )
        comment_in_new_post = Comment.objects.filter(post=new_post).first()
        self.assertEqual(test_comment, comment_in_new_post)
        response = self.auth_client.get('/posts/1/')
        self.assertNotIn(test_comment, response.context['comments'])
        response = self.auth_client.get('/posts/5/')
        self.assertIn(test_comment, response.context['comments'])

    def test_cache_is_working(self):
        '''Проверка кеширования главной страницы'''
        response = self.auth_client.get(self.HOME_URL['index'])
        Post.objects.all().delete()
        self.assertTrue(Post.objects.count() == 0)
        self.assertIn(self.post.text.encode(), response.content)

    def test_auth_user_can_follow(self):
        '''Авторизированный пользователь может подписаться и отписаться'''
        self.follower_client.get(self.HOME_URL['follow'])
        self.assertTrue(Follow.objects.filter(
            user=self.follower, author=self.user
        ).exists())
        self.assertTrue(Follow.objects.count() == 1)
        self.follower_client.get(self.HOME_URL['unfollow'])
        self.assertFalse(Follow.objects.filter(
            user=self.follower, author=self.user
        ).exists())
        self.assertTrue(Follow.objects.count() == 0)

    def test_post_is_in_favorite_newsline(self):
        '''Новая запись есть в ленте подписчиков и ее нет у остальных'''
        Follow.objects.create(user=self.follower, author=self.user)
        post = Post.objects.create(
            author=self.user, text='Проверка follow_index'
        )
        response = self.follower_client.get(self.HOME_URL['follow_index'])
        self.assertIn(post, response.context['page_obj'].object_list)
        response = self.auth_client.get(self.HOME_URL['follow_index'])
        self.assertNotIn(post, response.context['page_obj'].object_list)
