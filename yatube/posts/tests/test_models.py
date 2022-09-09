from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()
NUM_CHAR = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост jguygofugfwihirh',
        )

    def test_models_have_correct_object_names(self):
        group = PostModelTest.group
        expected_object_name = self.group.title
        self.assertEqual(expected_object_name, str(group))
        post = PostModelTest.post
        expected_name = self.post.text[:NUM_CHAR]
        self.assertEqual(expected_name, str(post))
