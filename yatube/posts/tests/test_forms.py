from django.test import Client, TestCase
from django.urls import reverse

from ..forms import forms
from ..models import Group, Post, User

CREATE_POST = reverse('posts:post_create')
USERNAME = 'tester'
PROFILE = reverse('posts:profile',
                  kwargs={'username': USERNAME})


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_1 = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug_1',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

        cls.EDITE_POST = reverse('posts:post_edit',
                                 kwargs={'post_id': cls.post.id})
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})

    def setUp(self):
        self.authorized_client = Client()  # Авторизованный
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        form_data = {
            'text': 'text',
            'group': self.group.pk,
        }
        """Тестирование создания поста"""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            CREATE_POST,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        posts = Post.objects.exclude(id=self.post.id)
        self.assertEqual(len(posts), 1)
        post = posts[0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertRedirects(response, PROFILE)

    def test_editing_post(self):
        form_data = {
            'text': 'TEST',
            'group': self.group_1.pk,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            self.EDITE_POST,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(post.author, self.user)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_post_posts_edit_page_show_correct_context(self):
        templates_url_names = [
            self.EDITE_POST,
            CREATE_POST,
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for url in templates_url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_field, expected)
