from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.conf import settings

from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm


def page_breakdown(page_number, objects):
    paginator = Paginator(objects, settings.COUNT_POST)
    return paginator.get_page(page_number)


def index(request):
    """Выводит шаблон главной страницы."""
    posts = Post.objects.select_related(
        'author', 'group'
    )
    page_number = request.GET.get('page')
    context = {
        'page_obj': page_breakdown(page_number, posts)
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_number = request.GET.get('page')
    context = {
        'group': group,
        'posts': posts,
        'show_groups': False,
        'page_obj': page_breakdown(page_number, posts)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профайла пользователя"""
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    page_number = request.GET.get('page')
    context = {
        'author': author,
        'following': request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user, author=author
        ).exists(),
        'page_obj': page_breakdown(page_number, posts),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Выводит шаблон страницы поста."""
    post = get_object_or_404(
        Post.objects.select_related(), pk=post_id
    )
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm()
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    """Обрабатывает создания поста."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    """Выводит шаблон создания поста."""
    form_post = PostForm(request.POST or None)
    if form_post.is_valid():
        form = form_post.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user.username)
    context = {
        'form': form_post,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Выводит шаблон редактирования поста."""
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()

        return redirect('posts:post_detail', post_id=post.id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def follow_index(request):
    posts_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related(
        'author', 'group'
    )
    page_number = request.GET.get('page')
    context = {'page_obj': page_breakdown(page_number, posts_list)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author__username=username
    ).delete()
    return redirect('posts:profile', username=username)
