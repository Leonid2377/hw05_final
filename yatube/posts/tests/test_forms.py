import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

USERNAME = 'NoName'
USERNAME_2 = 'NotAuthor'
POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
TEXT_COMMENT = 'Текст коммент'
TEXT_CREATE = 'Текст создать'
TEXT_EDIT = 'Текст редактировать'


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username=USERNAME_2)
        cls.guest_client = Client()
        cls.not_author_client = Client()
        cls.authorized_client = Client()
        cls.not_author_client.force_login(cls.user2)
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тест заголовок',
            slug='test-slug',
            description='Тест описание',
        )
        cls.group2 = Group.objects.create(
            title='Тест заголовок 2',
            slug='test-slug2',
            description='Тест описание 2',
        )
        cls.form = PostForm()

    def setUp(self):
        self.post = Post.objects.create(
            author=self.user,
            group=self.group,
            text='Тестовый текст',
        )
        self.POST_EDIT_URL = reverse('posts:post_edit', args=[self.post.pk])
        self.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=[self.post.pk]
        )
        self.COMMENT_CREATE_URL = reverse(
            'posts:add_comment', args=[self.post.pk]
        )

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        Post.objects.all().delete()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': TEXT_CREATE,
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.all()[0]
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(
            post.image.name, f'{ settings.UPLOAD_TO }{ uploaded.name }'
        )
        self.assertEqual(post.author, self.user)

    def test_edit_post(self):
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': TEXT_EDIT,
            'group': self.group2.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(
            post.image.name, f'{ settings.UPLOAD_TO }{ uploaded.name }'
        )
        self.assertEqual(post.author, self.post.author)

    def test_post_create_or_edit_page_show_correct_context(self):
        addresses = [
            POST_CREATE_URL,
            self.POST_EDIT_URL,
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                    'image': forms.fields.ImageField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = (
                            response.context.get('form').fields.get(value)
                        )
                        self.assertIsInstance(form_field, expected)

    def test_comment_appears_on_post_page_after_successfully_adding(self):
        self.post.comments.all().delete()
        form_data = {
            'text': TEXT_COMMENT
        }
        response = self.authorized_client.post(
            self.COMMENT_CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.post.comments.count(), 1)
        comment = self.post.comments.all()[0]
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_not_author_or_guest_client_edit_post(self):
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        user, text, group, image = (self.user, self.post.text,
                                    self.post.group, self.post.image)
        clients = [self.not_author_client, self.guest_client]
        form_data = {
            'text': TEXT_EDIT,
            'group': self.group2.pk,
            'image': uploaded
        }
        for client in clients:
            with self.subTest(client=client):
                response = client.post(
                    self.POST_EDIT_URL,
                    data=form_data,
                    follow=True,
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertEqual(self.post.author, user)
                self.assertEqual(self.post.text, text)
                self.assertEqual(self.post.group, group)
                self.assertEqual(self.post.image, image)

    def test_guest_client_create_post(self):
        Post.objects.all().delete()
        form_data = {
            'text': TEXT_CREATE,
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), 0)

    def test_guest_client_adding_comment(self):
        Comment.objects.all().delete()
        form_data = {
            'text': TEXT_COMMENT,
        }
        response = self.guest_client.post(
            self.COMMENT_CREATE_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), 0)

