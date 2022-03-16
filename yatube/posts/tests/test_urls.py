from http import HTTPStatus

from django.test import TestCase, Client
from django.core.cache import cache


from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.URLS_FOR_ALL = {
            'posts/index.html': '/',
            'about/tech.html': '/about/tech/',
            'about/author.html': '/about/author/',
            'posts/group_list.html': '/group/test/',
            'posts/profile.html': '/profile/auth/',
            'posts/post_detail.html': '/posts/1/',
        }
        cls.URLS_FOR_AUTH = {
            'posts/create_post.html': '/create/',
            'users/password_change_form.html': '/auth/password_change/',
        }
        cls.user = User.objects.create_user(username='auth')
        cls.author = Client()
        cls.author.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            pk=1,
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='loginned')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_page_urls_have_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        all_urls_for_test = self.URLS_FOR_ALL.copy()
        all_urls_for_test.update(self.URLS_FOR_AUTH)
        for template, url in all_urls_for_test.items():
            with self.subTest(field=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_page_urls_exists_for_guest(self):
        """Доступность адресов для анонимного пользователя"""
        for url in self.URLS_FOR_ALL.values():
            with self.subTest(field=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_urls_exists_for_authorised_users(self):
        """Доступность адресов для авторизированного пользователя"""
        all_urls_for_test = self.URLS_FOR_ALL.copy()
        all_urls_for_test.update(self.URLS_FOR_AUTH)
        for url in all_urls_for_test.values():
            with self.subTest(field=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_autrorised_url_redirect_to_login(self):
        """Редирект анонимного пользователя на страницу логина."""
        for url in self.URLS_FOR_AUTH.values():
            with self.subTest(field=url):
                redirect_url = f'/auth/login/?next={url}'
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect_url)

    def test_author_urls_exists_for_author_only(self):
        """Страницы, доступные только автору."""
        tested_urls = {
            'Редактирование своего поста': '/posts/1/edit/',
        }
        for field, url in tested_urls.items():
            with self.subTest(field=field):
                response_200 = self.author.get(url)
                self.assertEqual(response_200.status_code, HTTPStatus.OK)
                response_302 = self.authorized_client.get(url)
                self.assertEqual(response_302.status_code, HTTPStatus.FOUND)
                response_302g = self.guest_client.get(url)
                self.assertEqual(response_302g.status_code, HTTPStatus.FOUND)

    def test_invalid_urls_404_response(self):
        """Несуществующие ссылки ведут на страницу 404."""
        tested_urls = {
            'Несуществующий пост': '/posts/sdfa/',
            'Несуществующая группа': '/group/111/',
            'Несуществующий автор': '/profile/sadff/',
            'Несуществующая страница': '/unexisting_page',
        }
        for field, url in tested_urls.items():
            with self.subTest(field=field):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_errors(self):
        """404 использует кастомный шаблон."""
        errors_test = {
            'core/404.html': '/unexisting_page/',
        }
        for template, url in errors_test.items():
            with self.subTest(field=template):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
