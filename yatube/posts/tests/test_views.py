import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SLUG = 'test-slug'
FOREIGN_SLUG = 'test-slug2'
USERNAME = 'NoName'
USERNAME_2 = 'NoName2'
GROUP_LIST_URL = reverse('posts:group', args=[SLUG])
FOREIGN_GROUP_LIST_URL = reverse('posts:group', args=[FOREIGN_SLUG])
INDEX_URL = reverse('posts:index')
PROFILE_URL = reverse('posts:profile', args=[USERNAME_2])
FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME_2])
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME_2])
FOLLOW_INDEX_URL = reverse('posts:follow_index')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user2 = User.objects.create_user(username=USERNAME_2)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client2 = Client()
        cls.authorized_client2.force_login(cls.user2)
        cls.group = Group.objects.create(
            title='Тест заголовок',
            slug=SLUG,
            description='Тест описание',
        )
        cls.group2 = Group.objects.create(
            title='Тест заголовок',
            slug=FOREIGN_SLUG,
            description='Тест описание',
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тест текст',
            author=cls.user2,
            group=cls.group,
            image=uploaded,
        )
        cls.POST_EDIT_URL = reverse('posts:post_edit', args=[cls.post.pk])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.pk])
        Follow.objects.create(user=cls.user, author=cls.user2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        addresses = [
            PROFILE_URL,
            self.POST_DETAIL_URL,
            GROUP_LIST_URL,
            INDEX_URL,
            FOLLOW_INDEX_URL,
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                if address == self.POST_DETAIL_URL:
                    post = response.context['post']
                else:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_profile_page_show_correct_author(self):
        response = self.authorized_client.get(PROFILE_URL)
        self.assertEqual(response.context['author'], self.user2)

    def test_group_list_page_show_correct_group(self):
        response = self.authorized_client.get(GROUP_LIST_URL)
        group = response.context['group']
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)

    def test_first_page_contains_expected_number_of_records(self):
        for post in range(settings.NUM_POSTS):
            Post.objects.create(
                text='Тест текст',
                author=self.user2,
                group=self.group,
            )
        addresses = (
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL,
        )
        for address in addresses:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), settings.NUM_POSTS
                )

    def test_second_page_contains_one_record(self):
        for post in range(settings.NUM_POSTS):
            Post.objects.create(
                text='Тест текст',
                author=self.user,
                group=self.group,
            )
        addresses = (
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL,
        )
        for address in addresses:
            with self.subTest(address=address):
                response = self.authorized_client.get(address + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_new_post_does_not_exist_in_foreign_group(self):
        response = self.authorized_client.get(FOREIGN_GROUP_LIST_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_cache_index(self):
        response = self.authorized_client.get(INDEX_URL).content
        Post.objects.create(
            author=self.user,
            text='Тестовый текст'
        )
        self.assertEqual(
            response, self.authorized_client.get(INDEX_URL).content
        )
        cache.clear()
        self.assertNotEqual(
            response, self.authorized_client.get(INDEX_URL).content
        )

    def test_authorized_user_can_follow_authors(self):
        Follow.objects.all().delete()
        self.authorized_client.get(FOLLOW_URL)
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.user2).exists()
        )

    def test_authorized_user_can_unfollow_authors(self):
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.user2).exists()
        )
        self.authorized_client.get(UNFOLLOW_URL)
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.user2).exists()
        )

    def test_new_record_not_appears_at_foreign_feed(self):
        foreign_page_obj = (
            self.authorized_client2.get(FOLLOW_INDEX_URL).context['page_obj']
        )
        self.assertNotIn(self.post, foreign_page_obj)
