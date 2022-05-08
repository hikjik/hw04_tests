from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="user")
        cls.group = Group.objects.create(
            title="title",
            slug="slug",
            description="description",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text="text",
        )

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostFormTests.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        user = PostFormTests.user
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
            reverse("posts:profile", kwargs={"username": user.username}),
        )

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=group,
                text=form_data["text"],
            ).exists()
        )

    def test_edit_post(self):
        posts_count = Post.objects.count()
        post = PostFormTests.post

        form_data = {
            "text": "Новый тестовый текст",
            "group": post.group.id,
        }
        response = self.auth_client.post(
            reverse("posts:post_edit", kwargs={"post_id": post.id}),
            data=form_data,
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": post.id}),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.get(id=post.id).text, form_data["text"]
        )
