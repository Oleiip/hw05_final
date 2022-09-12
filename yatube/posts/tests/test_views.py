from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django import forms
from posts.models import Post, Group, Follow

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
        first_object = response.context['post']
        self.assertEqual(first_object.id, self.post1.id)
        self.assertEqual(first_object.author.username, self.user1.username)
        self.assertEqual(first_object.group.title, self.group.title)
        self.assertTrue(first_object.image)

    def test_post_edit_and_post_create_page_show_correct_context(self):
        """Шаблоны с post запросом сформированы с правильным контекстом."""
        list_views = [
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post1.id})
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for view in list_views:
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    response = self.authorized_client.get(view)
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_if_post_have_group(self):
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

    def test_paginator_records(self):
        """
        На 1 страницу выводится 10 постов,
        На 2 страницу выводится 3 поста
        """
        list_data = {
            10: '',
            3: '?page=2',
        }
        list_views = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.user1.username})]
        for key, value in list_data.items():
            for reverse_name in list_views:
                with self.subTest(reverse_name=reverse_name, value=value):
                    response = self.guest_client.get(reverse_name + value)
                    self.assertEqual(len(response.context['page_obj']), key)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AUTHOR')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста'
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
        Post.objects.create(
            text='Новый текст',
            author=self.user,
            group=self.group
        )
        second_time = self.guest_client.get(self.INDEX)
        self.assertEqual(first_time.content, second_time.content)

        cache.clear()

        third_time = self.guest_client.get(self.INDEX)
        self.assertNotEqual(first_time.content, third_time.content)


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AUTHOR')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для комментария'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment(self):
        form_data = {
            'text': 'Тестовый коментарий',
        }
        response_post = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response_post.status_code, 200)
        self.assertRedirects(
            response_post,
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        response_get = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ))
        comment_object = response_get.context['comments'][0]
        self.assertEqual(comment_object.author.username, self.user.username)
        self.assertEqual(comment_object.text, form_data['text'])


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.follower = User.objects.create(username='follower')

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.follower)

        cache.clear()

    def test_follow_author(self):
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author.id, self.author.id)
        self.assertEqual(follow.user.id, self.follower.id)
        response = self.guest_client.post(reverse(
            'posts:profile_follow', kwargs={'username': self.author})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response, f'/auth/login/?next=/profile/{self.author}/follow/'
        )

    def test_unfollow_author(self):
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_authors_post_in_user_page(self):
        post = Post.objects.create(
            author=self.author,
            text="тестовый пост")
        Follow.objects.create(
            user=self.follower,
            author=self.author)
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_authors_post_not_in_not_followers_page(self):
        post = Post.objects.create(
            author=self.author,
            text="тестовый пост")
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
