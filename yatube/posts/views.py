from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .models import Post, User, Group
from .forms import PostForm

POSTS_PER_PAGE: int = 10


def page_obj(post_list, page_number):
    paginator = Paginator(post_list, POSTS_PER_PAGE)
    return paginator.get_page(page_number)


def index(request):
    post_list = Post.objects.select_related("group", "author").all()

    context = {
        "page_obj": page_obj(post_list, request.GET.get("page")),
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    post_list = Post.objects.select_related("author").filter(group=group).all()

    context = {
        "group": group,
        "page_obj": page_obj(post_list, request.GET.get("page")),
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)

    post_count = Post.objects.filter(author=author).count()

    post_list = (
        Post.objects
        .select_related("author", "group")
        .filter(author=author)
        .all())

    context = {
        "post_count": post_count,
        "author": author,
        "page_obj": page_obj(post_list, request.GET.get("page")),
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "group"), id=post_id)

    post_count = Post.objects.filter(author=post.author).count()

    context = {
        "post": post,
        "post_count": post_count,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()

        return redirect("posts:profile", username=request.user.username)

    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("author", "group"), id=post_id)

    if request.user != post.author:
        return redirect("posts:post_detail", post_id=post_id)

    form = PostForm(request.POST or None, instance=post)

    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)

    context = {
        "form": form,
        "is_edit": True,
    }
    return render(request, "posts/create_post.html", context)
