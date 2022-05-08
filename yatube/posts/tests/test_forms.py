from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_author = User.objects.create_user(username="user")
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

        self.user = User.objects.create_user(username="auth user")
        self.auth_client = Client()
        self.auth_client.force_login(self.user)

        self.post_author_client = Client()
        self.post_author_client.force_login(PostFormTests.post_author)

    def test_create_post_authorized_client(self):
        posts_count = Post.objects.count()
        group = PostFormTests.group
        form_data = {
            "text": "Тестовый текст",
            "group": group.id,
        }

        response = self.auth_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username}),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=group,
                text=form_data["text"],
            ).exists()
        )

    def test_create_post_redirect_anonymous(self):
        form_data = {
            "text": "Тестовый текст",
            "group": PostFormTests.group.id,
        }
        path = reverse("posts:post_create")
        response = self.guest_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("users:login") + "?next=" + path,
            status_code=302,
            target_status_code=200,
        )

    def test_edit_post_author_client(self):
        posts_count = Post.objects.count()
        post = PostFormTests.post
        form_data = {
            "text": "Новый тестовый текст",
            "group": post.group.id,
        }
        response = self.post_author_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post.id}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(post.text, form_data["text"])

    def test_edit_post_redirect_anonymous(self):
        post = PostFormTests.post
        form_data = {
            "text": "Новый тестовый текст",
            "group": post.group.id,
        }
        path = reverse("posts:post_edit", kwargs={"post_id": post.id})
        response = self.guest_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("users:login") + "?next=" + path,
            status_code=302,
            target_status_code=200,
        )

    def test_edit_post_redirect_authorized_not_author(self):
        post = PostFormTests.post
        form_data = {
            "text": "Новый тестовый текст",
            "group": post.group.id,
        }

        path = reverse("posts:post_edit", kwargs={"post_id": post.id})
        response = self.auth_client.post(path, data=form_data, follow=True)

        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
            status_code=302,
            target_status_code=200,
        )
