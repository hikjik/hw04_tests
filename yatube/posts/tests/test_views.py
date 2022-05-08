from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group
from ..views import POSTS_PER_PAGE

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TOTAL_POSTS_COUNT = 13
        cls.POSTS_PER_PAGE = POSTS_PER_PAGE

        cls.user = User.objects.create_user(username="test user")

        cls.group = Group.objects.create(
            title="title",
            slug="slug",
            description="description",
        )

        cls.posts = dict()
        for i in range(cls.TOTAL_POSTS_COUNT):
            post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text=f"text_{i}",
            )
            cls.posts[post.id] = post

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PostViewTests.user)

    def test_pages_uses_correct_template(self):
        post = list(PostViewTests.posts.values())[0]

        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": post.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": post.author.username}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": post.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        response = self.auth_client.get(reverse("posts:index"))

        self._check_post_list(response.context["page_obj"])

    def test_home_first_page_posts_count(self):
        response = self.client.get(reverse("posts:index"))

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.POSTS_PER_PAGE,
        )

    def test_home_second_page_posts_count(self):
        response = self.client.get(reverse("posts:index") + "?page=2")

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.TOTAL_POSTS_COUNT - PostViewTests.POSTS_PER_PAGE,
        )

    def test_group_list_page_show_correct_context(self):
        group = PostViewTests.group
        response = self.auth_client.get(
            reverse("posts:group_list", kwargs={"slug": group.slug})
        )

        self._check_post_list(response.context["page_obj"])
        self._assert_equal_groups(response.context["group"], group)

    def test_group_list_empty_post_list_for_new_group(self):
        new_group = Group.objects.create(
            title="new title",
            slug="new_slug",
            description="new description",
        )

        response = self.auth_client.get(
            reverse("posts:group_list", kwargs={"slug": new_group.slug})
        )

        self.assertEqual(len(response.context["page_obj"]), 0)
        self._assert_equal_groups(response.context["group"], new_group)

    def test_group_list_first_page_posts_count(self):
        group = PostViewTests.group
        response = self.auth_client.get(
            reverse("posts:group_list", kwargs={"slug": group.slug})
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.POSTS_PER_PAGE,
        )

    def test_group_list_second_page_posts_count(self):
        group = PostViewTests.group
        response = self.auth_client.get(
            reverse(
                "posts:group_list",
                kwargs={"slug": group.slug},
            )
            + "?page=2",
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.TOTAL_POSTS_COUNT - PostViewTests.POSTS_PER_PAGE,
        )

    def test_profile_page_show_correct_context(self):
        user = PostViewTests.user
        response = self.auth_client.get(
            reverse("posts:profile", kwargs={"username": user.username})
        )

        self._check_post_list(response.context["page_obj"])
        self._assert_equal_users(response.context["author"], user)
        self.assertEqual(
            response.context["post_count"],
            PostViewTests.TOTAL_POSTS_COUNT,
        )

    def test_profile_page_first_page_posts_count(self):
        user = PostViewTests.user
        response = self.auth_client.get(
            reverse("posts:profile", kwargs={"username": user.username})
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.POSTS_PER_PAGE,
        )

    def test_profile_page_second_page_posts_count(self):
        user = PostViewTests.user
        response = self.auth_client.get(
            reverse(
                "posts:profile",
                kwargs={"username": user.username},
            )
            + "?page=2"
        )

        self.assertEqual(
            len(response.context["page_obj"]),
            PostViewTests.TOTAL_POSTS_COUNT - PostViewTests.POSTS_PER_PAGE,
        )

    def test_post_detail_page_show_correct_context(self):
        post = list(PostViewTests.posts.values())[0]
        response = self.auth_client.get(
            reverse("posts:post_detail", kwargs={"post_id": post.id})
        )

        self._assert_equal_posts(response.context["post"], post)
        self.assertEqual(
            response.context["post_count"], PostViewTests.TOTAL_POSTS_COUNT
        )

    def test_post_edit_page_show_correct_context(self):
        post = list(PostViewTests.posts.values())[0]
        response = self.auth_client.get(
            reverse("posts:post_edit", kwargs={"post_id": post.id})
        )

        self.assertTrue(response.context["is_edit"])

        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        response = self.auth_client.get(reverse("posts:post_create"))

        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_appears_on_pages(self):
        user = PostViewTests.user
        group = PostViewTests.group

        form_data = {
            "text": "some text",
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

        paths = [
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": group.slug}),
            reverse("posts:profile", kwargs={"username": user.username}),
        ]
        for path in paths:
            response = self.auth_client.get(path)
            post = response.context["page_obj"][0]
            self.assertEqual(post.text, form_data["text"])
            self.assertEqual(post.group.id, form_data["group"])

    def test_created_post_not_appears_on_another_group_page(self):
        new_group = Group.objects.create(
            title="another title",
            slug="another_slug",
            description="another description",
        )

        form_data = {
            "text": "some text",
            "group": new_group.id,
        }
        response = self.auth_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                "posts:profile",
                kwargs={"username": PostViewTests.user.username},
            ),
        )

        path = reverse(
            "posts:group_list",
            kwargs={"slug": PostViewTests.group.slug},
        )
        for page in range(1, 3):
            response = self.auth_client.get(path + f"?page={page}")
            for post in response.context["page_obj"]:
                self.assertNotEqual(post.group.id, new_group.id)

    def _check_post_list(self, posts):
        for post in posts:
            self._assert_equal_posts(post, PostViewTests.posts[post.id])

    def _assert_equal_posts(self, post_first, post_second):
        self._assert_equal_users(post_first.author, post_second.author)
        self._assert_equal_groups(post_first.group, post_second.group)
        self.assertEqual(post_first.text, post_second.text)

    def _assert_equal_groups(self, group_first, group_second):
        self.assertEqual(group_first.title, group_second.title)
        self.assertEqual(group_first.slug, group_second.slug)
        self.assertEqual(group_first.description, group_second.description)

    def _assert_equal_users(self, user_first, user_second):
        self.assertEqual(user_first.username, user_second.username)
