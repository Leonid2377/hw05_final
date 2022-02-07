from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый тeкст' * 100,
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        self.assertEqual(str(self.group), self.group.title)
        self.assertEqual(str(self.post), self.post.text[:15])
