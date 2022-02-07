import shutil
import tempfile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import User, Post, Group, Follow, Comment
from ..settings import NUMBER_POSTS_ON_PAGE

USERNAME = 'tester'
SLUG = 'test-slug'
SLUG_1 = 'test-slug_1'
INDEX = reverse('posts:index')
GROUP = reverse('posts:group',
                kwargs={'slug': SLUG})
GROUP_1 = reverse('posts:group',
                  kwargs={'slug': SLUG_1})
PROFILE = reverse('posts:profile',
                  kwargs={'username': USERNAME})
TOTAL_POSTS = NUMBER_POSTS_ON_PAGE + 1
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG,
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
            image=UPLOADED
        )
        cls.POST_DETAIL = reverse('posts:post_detail',
                                  kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()  # Гость
        self.authorized_client = Client()  # Авторизованный
        self.authorized_client.force_login(self.user)

    def test_post_not_in_another_group(self):
        '''Проверяем что пост не в другой группе'''
        response = self.authorized_client.get(GROUP_1)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_in_group(self):
        '''Проверяем что пост в нужной группе,
        появился на главной странице, '''
        responses = [
            [INDEX, 'page_obj'],
            [GROUP, 'page_obj'],
            [PROFILE, 'page_obj'],
            [self.POST_DETAIL, 'post'],
        ]
        for url, obj in responses:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if obj == 'page_obj':
                    posts = response.context[obj]
                    self.assertEqual(len(posts), 1)
                    post = posts[0]
                elif obj == 'post':
                    post = response.context['post']
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.pk, self.post.pk)
        response = self.guest_client.get(INDEX)
        obj = response.context['page_obj'][0]
        expected_image = obj.image
        self.assertEqual(expected_image, self.post.image)

    def test_author_in_context_profile(self):
        '''Автор в контексте профиля'''
        response = self.authorized_client.get(PROFILE)
        self.assertEqual(response.context['author'], self.user)

    def test_group_in_context_group(self):
        '''Группа в контексте Групп-ленты'''
        response = self.authorized_client.get(GROUP)
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(response.context['group'].description,
                         self.group.description
                         )

    def test_cache_index(self):
        """Проверка cache index.html"""
        response = self.authorized_client.get(INDEX)
        post = Post.objects.create(
            text=self.post.text,
            author=self.post.author
        )
        page = response.content
        self.assertEqual(page, response.content)
        post.delete()
        response = self.client.get(INDEX)
        cache.clear()
        self.assertNotEqual(response, response.content)

    def test_follow_unfollow(self):
        Comment.objects.create(
            post=self.post,
            text='test',
            author=self.user,
        )
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse('posts:profile_follow',
                    kwargs={'username': self.follower})
        )
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.follower).exists())
        self.assertEqual(Follow.objects.count(), follow_count + 1)

        self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.follower})
        )
        self.assertEqual(Follow.objects.count(), follow_count)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.follower).exists())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tester')
        Post.objects.bulk_create([
            Post(
                text='Тестовый текст',
                author=cls.user,
            ) for i in range(TOTAL_POSTS)
        ])

    def test_first_page_contains_records(self):
        response = self.client.get(INDEX)
        self.assertEqual(len(response.context['page_obj']),
                         NUMBER_POSTS_ON_PAGE)

    def test_second_page_contains_records(self):
        response = self.client.get(f'{INDEX}?page=2')
        calculation_len_obj = len(response.context['page_obj'])
        calculation_obj = TOTAL_POSTS % NUMBER_POSTS_ON_PAGE
        self.assertEqual(calculation_len_obj, calculation_obj)

