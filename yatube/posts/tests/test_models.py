from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_model_post_have_correct_object_name(self):
        self.assertEqual(self.post.text[:15], str(self.post))

    def test_model_group_have_correct_object_name(self):
        self.assertEqual(self.group.title, str(self.group))