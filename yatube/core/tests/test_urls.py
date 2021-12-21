from django.test import TestCase, Client


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.URLS_FOR_TEST = {
            'core/404.html': '/unexisting_page/',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_404_errors(self):
        """404 использует кастомный шаблон."""
        for template, url in self.URLS_FOR_TEST.items():
            with self.subTest(field=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
