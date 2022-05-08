from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username="post author")
        cls.group = Group.objects.create(
            title="title",
            slug="slug",
            description="description",
        )
        cls.post = Post.objects.create(
            author=cls.post_author,
            group=cls.group,
            text="text",
        )

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username="user")
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(PostURLTests.post_author)

    def test_public_urls_exists_at_desired_location(self):
        post = PostURLTests.post

        for path in [
            "/",
            f"/group/{post.group.slug}/",
            f"/profile/{post.author.username}/",
            f"/posts/{post.id}/",
        ]:
            with self.subTest(path=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url(self):
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_url_exists_at_desired_location_authorized(self):
        response = self.auth_client.get("/create/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous(self):
        response = self.guest_client.get("/create/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_post_edit_url_exists_at_desired_location_author(self):
        post = PostURLTests.post

        response = self.post_author_client.get(f"/posts/{post.id}/edit/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous(self):
        post = PostURLTests.post
        path = f"/posts/{post.id}/edit/"

        response = self.guest_client.get(path, follow=True)
        self.assertRedirects(response, "/auth/login/?next=" + path)

    def test_post_edit_url_redirect_authorized_not_author(self):
        post = PostURLTests.post

        response = self.auth_client.get(f"/posts/{post.id}/edit/", follow=True)
        self.assertRedirects(response, f"/posts/{post.id}/")

    def test_urls_uses_correct_template(self):
        post = PostURLTests.post

        for path, template in {
            "/": "posts/index.html",
            f"/group/{post.group.slug}/": "posts/group_list.html",
            f"/profile/{post.author.username}/": "posts/profile.html",
            f"/posts/{post.id}/": "posts/post_detail.html",
            f"/posts/{post.id}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }.items():
            with self.subTest(path=path):
                response = self.post_author_client.get(path)
                self.assertTemplateUsed(response, template)
