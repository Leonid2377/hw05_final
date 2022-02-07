from django.test import TestCase
from django.urls import reverse

POST_ID = 1
USERNAME = 'tester'
SLUG = 'test-slug'


class PostUrlTests(TestCase):

    def test_urls_uses_correct_route(self):
        routes = [
            ['/', 'index', None],
            [f'/group/{SLUG}/', 'group', [SLUG]],
            [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
            [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
            ['/create/', 'post_create', None],
            [f'/posts/{POST_ID}/edit/', 'post_edit', [POST_ID]],
        ]
        for url, name, arg in routes:
            self.assertEqual(url, reverse(f'posts:{name}', args=arg))
