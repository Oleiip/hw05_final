from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache
from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='lovely')
        cls.not_author = User.objects.create_user(username='pilly')
        cls.group = Group.objects.create(
            title='someee',
            slug='some_people',
            description='everyyy some day'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_get_pages(self):
        templates_url_names = ([
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.pk}/'])

        for address in templates_url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_get_pages_authorized(self):
        templates_url_names_authorized = ([
            '/create/',
            f'/posts/{self.post.pk}/edit/'])

        for address in templates_url_names_authorized:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_task_edit_url_redirect_not_author(self):
        self.authorized_client.force_login(self.not_author)
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(response,
                             f'/posts/{self.post.pk}/')

    def test_task_create_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response,
            reverse('users:login') + "?next=" + '/create/')

    def test_task_add_comment_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/comment/',
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login')
            + "?next=" + f'/posts/{self.post.pk}/comment/'
        )

    def test_task_profile_follow_redirect_anonymous_on_admin_login(self):
        list_views = [
            f'/profile/{self.user.username}/follow/',
            f'/profile/{self.user.username}/unfollow/'
        ]

        for reverse_name in list_views:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.post(reverse_name)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(
                    response,
                    reverse('users:login')
                    + "?next=" + reverse_name
                )

    def test_unknown_puth_return_404(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='oleiip')
        cls.group = Group.objects.create(
            title='someee',
            slug='some_people',
            description='everyyy some day'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
