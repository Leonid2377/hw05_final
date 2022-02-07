from django.test import Client, TestCase
from django.urls import reverse
# from django.conf.urls import handler404
from http import HTTPStatus

from ..models import Group, Post, User

USERNAME = 'tester'
USERNAME_2 = 'tester_2'
SLUG = 'test-slug'
INDEX = reverse('posts:index')
GROUP = reverse('posts:group',
                kwargs={'slug': SLUG})
PROFILE = reverse('posts:profile',
                  kwargs={'username': USERNAME})
CREATE_POST = reverse('posts:post_create')
UNEXISTING = '/posts/unexisting/'
LOGIN_REDIRECT = reverse('users:login')


class PostUrlTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(username=USERNAME_2)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})

        cls.EDITE_POST = reverse('posts:post_edit',
                                 kwargs={'post_id': cls.post.id})

    def setUp(self):
        self.author = Client()
        self.author.force_login(self.user)
        self.guest = Client()
        self.another = Client()
        self.another.force_login(self.user_2)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон для пользователя."""

        templates_url_names = [
            [INDEX, 'posts/index.html'],
            [GROUP, 'posts/group_list.html'],
            [PROFILE, 'posts/profile.html'],
            [self.POST_DETAIL, 'posts/post_detail.html'],
            [CREATE_POST, 'posts/create_post.html'],
            [self.EDITE_POST, 'posts/create_post.html'],
        ]
        for url, template in templates_url_names:
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author.get(url), template
                )

    def test_urs_exists_at_desired_location_guest(self):
        """Проверка доступа на станицы, авторизированного пользователя и
        гостя"""
        templates_url_names = [
            [INDEX, self.guest, HTTPStatus.OK],
            [GROUP, self.guest, HTTPStatus.OK],
            [PROFILE, self.guest, HTTPStatus.OK],
            [self.POST_DETAIL, self.guest, HTTPStatus.OK],
            [CREATE_POST, self.guest, HTTPStatus.FOUND],
            [CREATE_POST, self.author, HTTPStatus.OK],
            [self.EDITE_POST, self.author, HTTPStatus.OK],
            [self.EDITE_POST, self.guest, HTTPStatus.FOUND],
            # [UNEXISTING, self.guest, HTTPStatus.NOT_FOUND],
        ]
        for url, user, answer in templates_url_names:
            with self.subTest(url=url):
                self.assertEqual(user.get(url).status_code, answer)

    def test_urls_redirect(self):
        urls_names = [
            [CREATE_POST, self.guest, f'{LOGIN_REDIRECT}?next=/create/'],
            [self.EDITE_POST, self.another, self.POST_DETAIL],
            [self.EDITE_POST,
             self.guest, f'{LOGIN_REDIRECT}?next={self.EDITE_POST}']
        ]
        for url, user, redirect in urls_names:
            with self.subTest(url=url):
                self.assertRedirects(user.get(url), redirect)

    # def test_template_error_page(self):
    #     response = self.client.get(UNEXISTING)
    #     self.assertTemplateUsed(response, ('core/404.html'))
