from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django import forms
from posts.models import Post, Group, Comment

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user1 = User.objects.create_user(username='oleiip')
        cls.user2 = User.objects.create_user(username='fany')
        cls.group = Group.objects.create(
            title='someee',
            slug='some_people',
            description='everyyy some day'
        )
        cls.group2 = Group.objects.create(
            title='sale',
            slug='people',
            description='some day'
        )
        cls.post1 = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post1,
            author=cls.user1,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user1.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post1.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post1.id}
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertTrue(len(response.context['page_obj']))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author.username, self.user1.username)
        self.assertEqual(first_object.text, self.post1.text)
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertTrue(first_object.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ))
        self.assertIn('page_obj', response.context)
        self.assertTrue(len(response.context['page_obj']))
        self.assertIn('group', response.context)
        first_object = response.context['page_obj'][0]
        group_object = response.context['group']
        self.assertEqual(first_object.group.id, self.group.id)
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertEqual(first_object.group.slug, self.group.slug)
        self.assertTrue(first_object.image)
        self.assertEqual(group_object.id, self.group.id)
        self.assertEqual(group_object.title, self.group.title)
        self.assertEqual(group_object.slug, self.group.slug)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user1.username}
                    ))
        self.assertIn('page_obj', response.context)
        self.assertTrue(len(response.context['page_obj']))
        self.assertIn('author', response.context)
        first_object = response.context['page_obj'][0]
        author_object = response.context['author']
        self.assertEqual(first_object.author.id, self.user1.id)
        self.assertEqual(first_object.author.username, self.user1.username)
        self.assertTrue(first_object.image)
        self.assertEqual(author_object.id, self.user1.id)
        self.assertEqual(author_object.username, self.user1.username)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post1.id}
                    ))
        self.assertIn('post', response.context)
        self.assertIn('comments', response.context)
        first_object = response.context['post']
        comment_object = response.context['comments'][0]
        self.assertEqual(first_object.id, self.post1.id)
        self.assertEqual(first_object.author.username, self.user1.username)
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertTrue(first_object.image)
        self.assertEqual(comment_object.text, self.comment.text)
        self.assertEqual(comment_object.author.username, self.user1.username)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post1.id}
                    ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_if_post_have_group(self):
        list_views = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user1.username})]

        for reverse_name in list_views:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                context = response.context['page_obj'].object_list
                self.assertIn(self.post1, context)

        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group2.slug})
        )
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post1, context)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='oleiip')
        cls.group = Group.objects.create(
            title='someee',
            slug='some_people',
            description='everyyy some day'
        )
        for post in range(13):
            Post.objects.create(
                author=cls.user1,
                text='Тестовый текст',
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """На страницу выводится 10 постов"""
        list_views = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user1.username})]

        for reverse_name in list_views:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """На 2 страницу выводится 3 поста"""
        list_views = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user1.username})]
        for reverse_name in list_views:
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class TestaCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AUTHOR')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Мой первый комментарий'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.guest_client = Client()
        self.INDEX = reverse('posts:index') 

    def test_cache_index(self):
        first_time = self.guest_client.get(self.INDEX)
        post_1 = Post.objects.create(
            text='Новый текст',
            author=self.user,
            group=self.group
        )
        second_time = self.guest_client.get(self.INDEX)
        self.assertEqual(first_time.content, second_time.content)

        cache.clear()

        third_time = self.guest_client.get(self.INDEX)
        self.assertNotEqual(first_time.content, third_time.content)
